from processpiper.text2diagram import render

if __name__ == '__main__':
    input_syntax = """
title: result20
width: 10000
colourtheme: BLUEMOUNTAIN
lane:
	(start) as start
	[receive expense report from employee] as activity_11
	[notify employee of report receipt] as activity_12
	<employee has no account?> as gateway_1
	[create new account for employee] as activity_3
	<> as gateway_1_end
	[review report for approval] as activity_13
	<automatic approval?> as gateway_2
	(end) as gateway_2_end
	[request manual approval] as activity_15
	<report is rejected?> as gateway_3
	[send rejection notice to employee] as activity_4
	<> as gateway_3_end
	[deposit reimbursement to employee's account] as activity_16
	[send approval notice to employee] as activity_17
	<employee requests rectification?> as gateway_4
	[register rectification request] as activity_19
	[review report post-rectification] as activity_20
	<> as gateway_4_end
	<report not handled in 30 days?> as gateway_5
	[terminate process] as activity_8
	[send cancellation notice to employee] as activity_9
	[employee resubmits report] as activity_10
	<> as gateway_5_end
	(end) as end

start->activity_11->activity_12->gateway_1
gateway_1-"yes"->activity_3->gateway_1_end
gateway_1-"no"->gateway_1_end
gateway_1_end->activity_13->gateway_2
gateway_2-"yes"->gateway_2_end
gateway_2-"no"->activity_15->gateway_3
gateway_3-"yes"->activity_4->gateway_3_end
gateway_3-"no"->activity_16->activity_17->gateway_4
gateway_4-"yes"->activity_19->activity_20->gateway_4_end
gateway_4-"no"->gateway_4_end
gateway_4_end->gateway_5
gateway_5-"yes"->activity_8->activity_9->activity_10->gateway_5_end
gateway_5-"no"->gateway_5_end
gateway_5_end->end
       """
    render(input_syntax, "/Users/shuaiwei_yu/Desktop/bachelor-thesis/project/Diagram/output_LLM/text20_bpmn.png")
