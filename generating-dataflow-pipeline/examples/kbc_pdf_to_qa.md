# Example: PDF to QA Pipeline (Knowledge Base Cleaning)

## User Request
"Extract QA pairs from PDF documents after cleaning and chunking"

## Sample Data
```jsonl
{"pdf_path": "/data/research_paper.pdf"}
{"pdf_path": "/data/technical_doc.pdf"}
```

## Response

### Intermediate Operator Decision
```json
{
  "ops": ["KBCCompositeCleaningFlashOperator", "Text2QAGenerator", "PromptedFilter"],
  "field_flow": "pdf_path -> cleaned_chunk -> question+answer -> quality_score",
  "reason": "Input is PDF file paths (not text content), so KBCCompositeCleaningFlashOperator is valid and necessary. Text2QAGenerator is domain-specific operator for QA construction. PromptedFilter evaluates answer field as practical proxy for QA pair quality (answer contains full context from generation). Field dependencies satisfied: pdf_path (sample) -> cleaned_chunk (KBC) -> question+answer (QA gen) -> quality_score (filter on answer)."
}
```

### 1. Field Mapping
```
Available in sample:
  - pdf_path (file path - valid for KBC)

To be generated:
  - cleaned_chunk (output from KBC step)
  - question (output from QA gen step)
  - answer (output from QA gen step)
  - qa_prompt (output from QA gen step)
  - quality_score (output from filter step)

Field flow:
  pdf_path → [KBC] → cleaned_chunk → [Text2QA] → question, answer → [Filter] → quality_score
```

### 2. Ordered Operator List
1. **KBCCompositeCleaningFlashOperator**: Clean and chunk PDFs
   - Why: Input is file path, need PDF→Markdown→Chunks→Cleaned pipeline
   - Input: pdf_path (exists in sample, is file path)
   - Output: cleaned_chunk

2. **Text2QAGenerator**: Generate QA pairs from chunks
   - Why: Domain-specific operator for QA construction
   - Input: cleaned_chunk (created by step 1)
   - Output: question, answer, qa_prompt

3. **PromptedFilter**: Filter by quality
   - Why: Need LLM evaluation of QA pair quality
   - Input: answer (used as practical proxy - answer field contains full Q+A context from Text2QAGenerator)
   - Output: quality_score
   - Filter: Keep only score >= 4
   - Note: Evaluating answer field is sufficient because Text2QAGenerator's answer output includes the full QA context

### 3. Reasoning Summary
- KBC is valid because input field is pdf_path (file path, not text content)
- Text2QAGenerator is preferred over generic PromptedGenerator for QA construction
- PromptedFilter evaluates answer field as practical proxy for QA pair quality
  - Rationale: Text2QAGenerator's answer output contains full Q+A context, making it sufficient for quality evaluation
  - Alternative would be to add a combination step, but filtering on answer directly is simpler and effective
- No additional prompt-driven generators needed beyond built-in operator capabilities
- Field dependencies properly ordered: each step consumes fields created by previous steps
- Total pipeline: 3 operators, semantically complete dataflow

### 4. Complete Standard Pipeline Code
```python
from dataflow.operators.core_text import Text2QAGenerator, PromptedFilter
from dataflow.operators.knowledge_cleaning import KBCCompositeCleaningFlashOperator
from dataflow.serving import APILLMServing_request
from dataflow.utils.storage import FileStorage

class PDFtoQAPipeline:
    def __init__(self):
        # Input file MUST be JSONL format (one JSON object per line):
        # {\"pdf_path\": \"/data/paper1.pdf\", \"source\": \"arxiv\"}
        # {\"pdf_path\": \"/data/paper2.pdf\", \"source\": \"conference\"}
        self.storage = FileStorage(
            first_entry_file_name="pdf_list.jsonl",
            cache_path="./cache_pdf_qa",
            file_name_prefix="pdf_step",
            cache_type="jsonl"
        )

        self.llm_serving = APILLMServing_request(
            api_url="https://api.openai.com/v1/chat/completions",
            model_name="gpt-4o",
            max_workers=10
        )

        self.kbc_cleaner = KBCCompositeCleaningFlashOperator(
            llm_serving=self.llm_serving,
            intermediate_dir="./kbc_intermediate/",
            # mineru_model_path: set to local MinerU model path if using MinerU backend; 
            mineru_model_path=None,
            chunk_size=512,
            chunk_overlap=50,
            lang="en"
        )

        self.qa_generator = Text2QAGenerator(
            llm_serving=self.llm_serving
        )

        self.qa_filter = PromptedFilter(
            llm_serving=self.llm_serving,
            system_prompt="Evaluate this QA pair quality on scale 1-5. Consider: question clarity, answer accuracy, answer completeness, relevance to source.",
            min_score=4,
            max_score=5
        )

    def forward(self):
        self.kbc_cleaner.run(
            storage=self.storage.step(),
            input_key="pdf_path",
            output_key="cleaned_chunk"
        )

        self.qa_generator.run(
            storage=self.storage.step(),
            input_key="cleaned_chunk",
            input_question_num=2,
            output_prompt_key="qa_prompt",
            output_question_key="question",
            output_answer_key="answer"
        )

        self.qa_filter.run(
            storage=self.storage.step(),
            input_key="answer",
            output_key="quality_score"
        )

if __name__ == "__main__":
    pipeline = PDFtoQAPipeline()
    pipeline.forward()
```

### 5. Adjustable Parameters / Caveats

**Tunable Parameters**:
- `chunk_size`: Increase to 1024 for longer context
- `chunk_overlap`: Increase to 100 for better continuity
- `input_question_num`: Change to 1 or 3 to control QA density
- `min_score`: Lower to 3 for more lenient filtering
- `lang`: Set to "zh" for Chinese documents
- `max_workers`: Increase for faster processing

**Fallback Strategies**:
- If < 30% pass filter: Increase chunk_size to 1024 for more context
- If questions too generic: Modify Text2QAGenerator configuration
- If answers incomplete: Increase chunk_size or adjust overlap

**Caveats**:
- KBCCompositeCleaningFlashOperator requires GPU for optimal performance
- Each PDF generates multiple chunks (N chunks × 2 QA = 2N pairs)
- Filter evaluates answer field which contains full QA context from generation

**Debugging**:
- Check `cache_pdf_qa/pdf_step_1.jsonl` for cleaned chunks
- Check `cache_pdf_qa/pdf_step_2.jsonl` for QA pairs
- Check `cache_pdf_qa/pdf_step_3.jsonl` for filtered results
- Monitor pass rate by comparing row counts
