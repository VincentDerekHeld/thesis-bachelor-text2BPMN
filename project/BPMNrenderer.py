from processpiper.text2diagram import render

if __name__ == '__main__':
    input_syntax = """
title: text2_our_approach
width: 10000
colourtheme: BLUEMOUNTAIN
lane: customer
	(start) as start
	[brings a defective computer] as activity_8
	[takes her computer] as activity_4
	(end) as end_4
	<> as gateway_1_end
	[execute two activities] as activity_11
	[the first activity check the hardware] as activity_12
	[the first activity repair the hardware] as activity_13
	[the second activity checks the software] as activity_14
	[the second activity configure the software] as activity_15
	[test the proper system functionality] as activity_16
	<detect an error?> as gateway_5
	[execute another arbitrary repair activity] as activity_7
	(end) as end_7
lane: crs
	[checks the defect] as activity_9
	[hand out a repair cost calculation] as activity_10
	<the costs are acceptable?> as gateway_1
	[the process continues] as activity_3

start->activity_8->activity_9->activity_10->gateway_1
gateway_1-"yes"->activity_3
gateway_1-"no"->activity_4->end_4
gateway_1_end->activity_11->activity_12->activity_13->activity_14->activity_15->activity_16->gateway_5
gateway_5-"yes"->activity_7->end_7
gateway_5-"no"
 """
    render(input_syntax, "/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/test.png")


" those for other specific processing situations = lane1.add_element("