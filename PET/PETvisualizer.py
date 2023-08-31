import json

# if __name__ == '__main__':
#     with open("text14.json") as file:
#         data = json.load(file)
#
#         width = 15
#
#         for i in range(len(data["tokens"])):
#             print(f"{data['tokens'][i]:{width}}{data['ner_tags'][i]}")

if __name__ == '__main__':
    with open("text15.json") as file:
        data = json.load(file)

        # red = '<span style="color: red;">'
        # blue = '<span style="color: blue;">'
        # green = '<span style="color: green;">'
        # orange = '<span style="color: orange;">'
        # brown = '<span style="color: brown;">'
        # purple = '<span style="color: purple;">'
        # end = '</span>'
        red = '\\textcolor{red}{'
        blue = '\\textcolor{blue}{'
        green = '\\textcolor{green}{'
        orange = '\\textcolor{orange}{'
        brown = '\\textcolor{brown}{'
        purple = '\\textcolor{purple}{'
        end = '}'

        result = ""
        for i in range(len(data["tokens"])):
            token = data['tokens'][i]
            if token == '``':
                token = '"'

            if data['ner_tags'][i] == 'O':
                result += token
            elif data['ner_tags'][i] in ['B-Actor', 'I-Actor']:
                result += blue + token + end
            elif data['ner_tags'][i] in ['B-Activity', 'I-Activity']:
                result += green + token + end
            elif data['ner_tags'][i] in ['B-Activity Data', 'I-Activity Data']:
                result += orange + token + end
            elif data['ner_tags'][i] in ['B-XOR Gateway', 'I-XOR Gateway', 'B-AND Gateway', 'I-AND Gateway']:
                result += red + token + end
            elif data['ner_tags'][i] in ['B-Condition Specification', 'I-Condition Specification']:
                result += brown + token + end
            elif data['ner_tags'][i] in ['B-Further Specification', 'I-Further Specification']:
                result += purple + token + end

            if i != len(data["tokens"]) - 1:
                if data['tokens'][i + 1] not in [',', '.', '!', '?', ':', ';']:
                    result += " "

        file_path = "example.txt"
        with open(file_path, "w") as file:
            file.write(result)
