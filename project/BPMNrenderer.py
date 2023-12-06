from processpiper.text2diagram import render

if __name__ == '__main__':
    input_syntax = """
title: text10_our_approach
width: 10000
colourtheme: BLUEMOUNTAIN
lane: data subject
	(start) as start
	<> as gateway_1
	[obtain confirmation as to whether or not personal data are] as activity_3
	[have the right] as activity_14
	<> as gateway_1_end
	[transfer personal data to a third country] as activity_15
	[have the right] as activity_16
lane: controller
	[confirm] as activity_5
	[access the personal data and the following information 1 . 	 the purposes of the processing 2 . 	 the categories of personal data 3 . 	 the recipients or categories of recipient] as activity_7
	[store the personal data for which] as activity_8
	[determine that period] as activity_9
	[request rectification or erasure of personal data or restriction of processing of personal data concerning the data subject] as activity_10
	[object to such processing] as activity_11
	[lodge a complaint with a supervisory authority] as activity_12
	[not collect the personal data] as activity_13
	[provide a copy of the personal data] as activity_17
	[charge a reasonable fee] as activity_18
	[provide the information] as activity_19
	[the right not affect the rights and freedoms of others] as activity_20
	[obtain a copy] as activity_21
	(end) as end

start->gateway_1
gateway_1-"not process personal data"->activity_3->gateway_1_end
gateway_1-"not process personal data"->activity_5->gateway_1_end
gateway_1-"process personal data"->activity_7->activity_8->activity_9->activity_10->activity_11->activity_12->activity_13->activity_14->gateway_1_end
gateway_1_end->activity_15->activity_16->activity_17->activity_18->activity_19->activity_20->activity_21->end

 """
    render(input_syntax, "/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent/evaluation/test.png")


" those for other specific processing situations = lane1.add_element("