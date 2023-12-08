from processpiper.text2diagram import render

if __name__ == '__main__':
    input_syntax = """
title: text1_our_approach
width: 10000
colourtheme: BLUEMOUNTAIN
lane: sales department
	(start) as start
	[receive order] as activity_9
	<> as gateway_1
	[accept order for customized bike] as activity_2
	[inform storehouse and engineering department] as activity_11
	[reject order for customized bike] as activity_3
	(end) as end_3
	[finish process instance] as activity_10
	(end) as end_10
	<> as gateway_1_end
	[ship bicycle] as activity_18
	(end) as end
	[finish process instance] as activity_19
	(end) as end
lane: storehouse
	[process part list of order] as activity_12
	[check required quantity of each part] as activity_13
	[reserve part] as activity_14
	[order part] as activity_15
	[repeat procedure for each item on part list] as activity_16
	<storehouse reserved every item of part list?> as gateway_4
lane: engineering department
	[prepare for assembling ordered bicycle] as activity_17
	[assemble bicycle] as activity_8
	<> as gateway_4_end

start->activity_9->gateway_1
gateway_1->activity_2->activity_11->gateway_1_end
gateway_1->activity_3->end_3->activity_10->end_10
gateway_1_end->activity_12->activity_13->activity_14->activity_15->activity_16->activity_17->gateway_4
gateway_4-yes->activity_8->gateway_4_end
gateway_4-no->gateway_4_end
gateway_4_end->activity_18->end->activity_19->end
 """
    render(input_syntax, "/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/test.png")


" those for other specific processing situations = lane1.add_element("