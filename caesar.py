def caesar_cypher(text: str):
    upper = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U",
             "V", "W", "X", "Y", "Z"]

    lower = []
    for letter in upper:
        lower.append(letter.lower())

    num = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]

    encrypted_text = ""
    for char in text:
        if char in upper:
            actual_position = upper.index(char)
            relative_position = actual_position + 5
            print(relative_position)
            if relative_position >= len(upper):
                final_position = relative_position - len(upper)
                encrypted_text += f"{upper[final_position]}"
            else:
                final_position = relative_position
                encrypted_text += f"{upper[final_position]}"
        if char in lower:
            actual_position = lower.index(char)
            relative_position = actual_position + 5
            print(relative_position)
            if relative_position >= len(upper):
                final_position = relative_position - len(lower)
                encrypted_text += f"{lower[final_position]}"
            else:
                final_position = relative_position
                encrypted_text += f"{lower[final_position]}"

    return encrypted_text

print(f"{caesar_cypher("Ahoj")}")