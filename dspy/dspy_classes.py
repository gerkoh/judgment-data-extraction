import dspy
import dsp
from dspy.teleprompt import BootstrapFewShot

class CoTWithHintModule(dspy.Module):
    def __init__(self, signature, hint):
        super().__init__()

        # Pass signature to ChainOfThought module
        self.generate_answer = dspy.ChainOfThoughtWithHint(signature)
        self.signature = signature
        self.hint = hint

    # Flow for answering questions using predictor and retrieval modules
    def forward(self, question):

        # Call the predictor on a particular input.
        *keys, last_key = self.signature.kwargs.keys()

        prediction = self.generate_answer(question=question, hint=self.hint, rationale_type=dsp.Type(
            prefix="Reasoning: Let's think step by step and not use any example specific reasoning in order to come up with a generic way to",
            desc="${produce the " + last_key + "}. In order to develop a generic process, we ..."))

        return dspy.Prediction(answer=prediction.answer)
    
class DSPyBootstrapFewShot:
    def __init__(self, signature, hint, example_question_list, example_answer_list):
        self.signature = signature
        self.hint = hint
        self.example_question_list = example_question_list
        self.example_answer_list = example_answer_list

    def compile(self):
        # Configure DSPy to use GPT-4
        gpt = dspy.OpenAI(model='gpt-3.5-turbo')

        dspy.settings.configure(lm=gpt)

        # Converting the human curated examples in DSPy Examples
        dspy_examples = []

        example_question_list = self.example_question_list
        example_answer_list = self.example_answer_list

        for example_question in example_question_list:
            example_answer = example_answer_list[example_question_list.index(
                example_question)]

            dspy_example = dspy.Example(
                question=example_question,
                answer=example_answer
            )

            dspy_examples.append(dspy_example)

        # Process the examples
        processed_dspy_examples = []

        # Tell DSPy that the 'question' field is the input. Any other fields are labels and/or metadata.
        for example in dspy_examples:
            processed_dspy_examples.append(example.with_inputs("question"))

        train_set = processed_dspy_examples[:len(processed_dspy_examples) // 2]
        eval_set = processed_dspy_examples[len(processed_dspy_examples) // 2:]

        # Define accuracy metric
        accuracy = dspy.evaluate.metrics.answer_exact_match

        # Define teleprompter
        bootstrap_optimiser = BootstrapFewShot(teacher_settings=dict(
            {'lm': gpt}, max_bootstrapped_demos=len(train_set), max_labeled_demos=len(train_set) * 4, metric=accuracy))

        # Compile!
        compile_bootstrap_optimiser = bootstrap_optimiser.compile(
            student=CoTWithHintModule(self.signature, self.hint), trainset=train_set, valset=eval_set)

        return compile_bootstrap_optimiser

class TestSignature(dspy.Signature):
    """Answer questions with short factoid answers."""

    question = dspy.InputField()
    answer = dspy.OutputField(desc="often between 1 and 5 words")