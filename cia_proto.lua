-- Create a new protocol named "CIA Datagram Protocol"
local cia_proto = Proto("CIA", "CIA Datagram Protocol")

-- Define protocol fields
local f_seq_num = ProtoField.uint8("cia.seq", "Sequence Number", base.DEC)
local f_frag_id = ProtoField.uint16("cia.frag_id", "Fragment ID", base.DEC)
local f_msg_type = ProtoField.uint8("cia.msg_type", "Message Type", base.DEC, {
    [0] = "TEXT",
    [1] = "FILE",
    [2] = "CTRL",
})
local f_flags = ProtoField.uint8("cia.flags", "Flags", base.DEC), {
    [0] = "K-A",
    [1] = "CONN",
    [2] = "ACK",
    [3] = "FIN",
    [4] = "NAME",
    [5] = "NACK",
    [6] = "FRAG",
    [7] = "DATA"

}
local f_frag_size = ProtoField.uint16("cia.frag_size", "Fragment Size", base.DEC)
local f_crc16 = ProtoField.uint16("cia.crc", "CRC16", base.HEX)
local f_data = ProtoField.bytes("cia.data", "Data")

-- Add the fields to the protocol
cia_proto.fields = { f_seq_num, f_frag_id, f_msg_type, f_flags, f_frag_size, f_crc16, f_data }

-- Define a unique color filter slot for message types
local CTRL_COLOR_SLOT = 1  -- Assign slot 1 for CTRL messages
local DATA_COLOR_SLOT = 2  -- Assign slot 2 for FILE and TEXT messages

-- Dissector function
function cia_proto.dissector(buffer, pinfo, tree)
    -- Minimum packet length check (at least 14 bytes: 12 header + 2 CRC)
    if buffer:len() < 9 then
        return
    end

    -- Set protocol column in Wireshark
    pinfo.cols.protocol = "CIA"

    -- Add CIA Protocol to the protocol tree
    local subtree = tree:add(cia_proto, buffer(), "CIA Datagram Protocol")

    -- Parse fields
    local seq_num = buffer(0, 1):uint()  -- Sequence Number (1 byte)
    local frag_id = buffer(1, 2):uint()  -- Fragment ID (2 bytes)
    local msg_type = buffer(3, 1):uint() -- Message Type (1 byte)
    local flags = buffer(4, 1):uint()    -- Flags (1 byte)
    local frag_size = buffer(5, 2):uint()  -- Fragment Size (2 bytes)

    -- Calculate dynamic data length
    local total_len = buffer:len()
    local data_len = total_len - 14  -- Total length minus header (12 bytes) and CRC (2 bytes)
    local data = nil
    if data_len > 0 then
        data = buffer(7, data_len)  -- Data starts after header (12 bytes)
    end

    -- Parse CRC16 (last 2 bytes)
    local crc16 = buffer(total_len - 2, 2):uint()

    -- Add fields to the protocol tree
    subtree:add(f_seq_num, buffer(0, 1)):append_text(" (Sequence Number: " .. seq_num .. ")")
    subtree:add(f_frag_id, buffer(1, 2)):append_text(" (Fragment ID: " .. frag_id .. ")")
    subtree:add(f_msg_type, buffer(3, 1)):append_text(" (" .. (msg_type == 0 and "TEXT" or msg_type == 1 and "FILE" or msg_type == 2 and "CTRL" or "UNKNOWN") .. ")")

    -- Format flags as decimal and add descriptive text
    local flags_str = ""
    if flags & 0x01 ~= 0 then flags_str = flags_str .. "K-A, " end
    if flags & 0x02 ~= 0 then flags_str = flags_str .. "CONN, " end
    if flags & 0x04 ~= 0 then flags_str = flags_str .. "ACK, " end
    if flags & 0x08 ~= 0 then flags_str = flags_str .. "FIN, " end
    if flags & 0x10 ~= 0 then flags_str = flags_str .. "NAME, " end
    if flags & 0x20 ~= 0 then flags_str = flags_str .. "NACK, " end
    if flags & 0x40 ~= 0 then flags_str = flags_str .. "FRAG, " end
    if flags & 0x80 ~= 0 then flags_str = flags_str .. "DATA, " end

    -- Remove last comma and space if any
    if #flags_str > 0 then
        flags_str = string.sub(flags_str, 1, #flags_str - 2)  -- Remove trailing comma and space
    end

    subtree:add(f_flags, buffer(4, 1)):append_text(" (Flags: " .. flags .. " (" .. flags_str .. "))")
    subtree:add(f_frag_size, buffer(5, 2)):append_text(" (Fragment Size: " .. frag_size .. ")")
    subtree:add(f_crc16, buffer(total_len - 2, 2)):append_text(" (CRC16: 0x" .. string.format("%04X", crc16) .. ")")

    -- Add data to the tree (if present)
    if data_len > 0 then
        subtree:add(f_data, data):append_text(" (" .. data_len .. " bytes of Data)")
    end

    -- Colorize data and control messages
    -- Add custom coloring rules based on message type
    if msg_type == 2 then
        -- CTRL Message
        pinfo.cols.info:append(string.format(" [CTRL | Seq=%d | Frag=%d]", seq_num, frag_id))
        pinfo.private["color_filter_slot"] = CTRL_COLOR_SLOT
    elseif msg_type == 1 or msg_type == 0 then
        -- FILE and TEXT Messages
        local msg_label = (msg_type == 1) and "FILE" or "TEXT"
        pinfo.cols.info:append(string.format(" [%s | Seq=%d | Frag=%d]", msg_label, seq_num, frag_id))
        pinfo.private["color_filter_slot"] = DATA_COLOR_SLOT
    end
end

-- Register the dissector with UDP ports
local udp_table = DissectorTable.get("udp.port")
udp_table:add(12345, cia_proto)  -- Register for port 12345
udp_table:add(12344, cia_proto)  -- Register for port 12344
udp_table:add(54321, cia_proto)  -- Register for port 54321
udp_table:add(54320, cia_proto)  -- Register for port 54320
