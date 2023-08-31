import BPMNStarter

# if __name__ == '__main__':
#     BPMNStarter.start_task('Text/text_input/text16.txt', "result16", "/Users/shuaiwei_yu/Desktop/bachelor-thesis/project/Diagram/output_LLM/text16_bpmn.png")

def reformat(string: str):
    string = string.replace(".", "->")
    string = string.replace("\n", "), (")
    string = "(" + string
    string = string + ")"
    string = string.replace("(), ", "")
    string = string.replace(", ()", "")
    return string

if __name__ == '__main__':
    target = """
(1, 2), (1, 3), (2, 5), (3, 4), (4, 6), (4, 7), (7, 13), (6, 8), (6, 9), (8, 10), (9, 11), (10, 12), (11, 12), (10, 13), (11, 13), (13, 14)
"""
    output = """
(1, 2), (1, 3), (2, 5), (3, 4), (4, 6), (6, 9), (6, 8), (9, 11), (8, 10), (11, 7), (10, 7), (7, 13), (13, 4)
    """

    target = reformat(target)
    print("target:" + target)
    output = reformat(output)
    print("output:" + output)

    target = target.split(",")
    target_count = len(target)
    output = output.split(",")
    output_count = len(output)

    for i in reversed(output):
        if i in target:
            target.remove(i)
            output.remove(i)

    print("precision = " + str((output_count - len(output)) / output_count))
    print("recall = " + str((target_count - len(target)) / target_count))


