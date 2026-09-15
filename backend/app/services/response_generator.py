from backend.app.services.prompt_builder import build_financial_explanation_prompt
from backend.app.services.llm_service import ask_llm
from backend.app.services.response_validator import ResponseValidator

def generate_explanation(financial_result, question=None):
    intent = financial_result.get("intent", "GENERAL_FINANCE")
    fallback = ResponseValidator.get_deterministic_fallback(financial_result, intent, question=question or "")
    
    prompt = build_financial_explanation_prompt(financial_result, question=question)
    response = ask_llm(prompt, fallback_text=fallback)
    
    # Validate LLM output against deterministic facts
    is_valid, validation_reason = ResponseValidator.validate(response, financial_result, intent)
    if not is_valid:
        # Contradiction detected: return deterministic explanation guaranteed to be 100% accurate
        return fallback
    
    return response
