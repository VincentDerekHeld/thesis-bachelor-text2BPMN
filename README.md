# An enhanced automated approach for transforming natural language process descriptions to BPMN2.0 process diagrams – with an evaluation of the application to ISO-Norm process descriptions

This is the code of the bachelor thesis of [Vincent Derek Held](mailto:vincent.held@tum.de), written at the chair
of [Information Systems and Business Process Management at the Technical University of Munich (TUM)](https://www.cs.cit.tum.de/bpm/chair/).
The Thesis was written under the supervision of [Catherine Sai](mailto:catherine.sai@tum.de) and
under [Prof. Dr. Stefanie Rinderle-Ma](mailto:stefanie.rinderle-ma@tum.de) and can be found in this repository.

Since this work is based on the approach of [Shuaiwei YU](https://github.com/ShuaiweiYu/text2BPMN), in this repository
is also published code from him.

## Abstract

A comprehensive understanding of business processes is crucial for the digitization of these processes. The utilization
of Business Process Model and Notation (BPMN) 2.0 process diagrams has emerged as a pivotal tool in both research and
industry for representing and analyzing business workflows. These processes are influenced by an ever growing amount of
regulatory documents and process execution data.

This thesis is a contribution to develop a state-of-the-art approach for transforming natural language process
descriptions to BPMN2.0 process diagrams. The aim is to evaluate how recent developments have evolved compared to
existing methods and how well the approach works for process descriptions from more complex regulatory documents (e.g.
ISO standards or data protection regulations). Furthermore, it will be investigated which technologies are best suited
to extract information and how to visualize the process in a BPMN2.0 process model.

Keywords: Natural Language Processing, Business Process Compliance, Natural Language to Process, Business Process Model
Generation

## Installation:

1. Download the gitHub repository
2. Install the required packages with the right version:

```      
pip install -r requirements.txt
```

3. Run the Setup.py to download all benepar dependencies:

```
python  project/Setup.py
```

4. [Set OPENAI_API_KEY as Environment Variable for the LLM](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)
5. Set the Base Path variable to project folder in project/Constants.py:

```
BASE_PATH = "/Users/vincentderekheld/PycharmProjects/text2BPMN-vincent"
```

## Execution:

1. Enter the input path to the textual description  (.txt), to use it as an input file or use the default
2. Enter the output path, where the generated diagram should be stored (.png) or use the default
3. Execute the "main" methode in the "main.py" file

## FAQs or Common Issues

1. tbd.
2. tbd.
3. tbd.