"""
LLM Service - Flexible AI integration supporting multiple providers.
Supports: OpenAI, Anthropic, Ollama (via LiteLLM)
"""
import os
from flask import current_app


def get_llm_client():
    """Get the configured LLM client based on environment settings."""
    provider = os.environ.get('LLM_PROVIDER', 'openai')
    api_key = os.environ.get('LLM_API_KEY', '')
    model = os.environ.get('LLM_MODEL', 'gpt-3.5-turbo')

    return {
        'provider': provider,
        'api_key': api_key,
        'model': model
    }


def generate_summary(issue, expert_inputs):
    """
    Generate an AI summary of expert inputs for an issue.

    Args:
        issue: The Issue object
        expert_inputs: List of Comment objects with expert inputs

    Returns:
        str: Generated summary text
    """
    config = get_llm_client()

    # Check if API key is configured
    if not config['api_key']:
        return _generate_placeholder_summary(issue, expert_inputs)

    try:
        import litellm

        # Build the prompt
        prompt = _build_summary_prompt(issue, expert_inputs)

        # Call the LLM
        response = litellm.completion(
            model=config['model'],
            messages=[
                {
                    "role": "system",
                    "content": """You are a skilled facilitator helping engineering teams reach consensus on technical issues.
Your role is to:
1. Summarize all expert inputs into a coherent overview
2. Use diplomatic, constructive language (hard on the problem, soft on people)
3. Identify areas of agreement between experts
4. Identify areas that need clarification or further discussion
5. Generate specific, actionable questions for each expert to help reach consensus

Always maintain a professional, solution-oriented tone."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            api_key=config['api_key']
        )

        return response.choices[0].message.content

    except ImportError:
        return _generate_placeholder_summary(issue, expert_inputs)
    except Exception as e:
        raise Exception(f"LLM API error: {str(e)}")


def _build_summary_prompt(issue, expert_inputs):
    """Build the prompt for the LLM."""
    prompt = f"""## Issue: {issue.title}

### Problem Description:
{issue.description}

### Expert Inputs:
"""
    for comment in expert_inputs:
        expert_name = comment.author.username if comment.author else "Unknown"
        expert_role = comment.author.expert_role.name if comment.author and comment.author.expert_role else "Unknown Role"
        prompt += f"""
**{expert_name} ({expert_role}):**
{comment.content}
"""

    prompt += """
---

Please provide:
1. A consolidated summary of all expert perspectives (2-3 paragraphs)
2. Key areas of agreement
3. Areas needing clarification or further discussion
4. Specific questions for each expert to help reach consensus

Remember to use diplomatic language that is "hard on the problem, soft on people"."""

    return prompt


def _generate_placeholder_summary(issue, expert_inputs):
    """Generate a placeholder summary when LLM is not configured."""
    summary = """## AI Summary (Demo Mode)

**Note: LLM API key not configured. This is a placeholder summary.**

### Overview
"""
    for i, comment in enumerate(expert_inputs, 1):
        expert_name = comment.author.username if comment.author else "Unknown"
        expert_role = comment.author.expert_role.name if comment.author and comment.author.expert_role else "Unknown Role"
        # Truncate long inputs
        input_preview = comment.content[:200] + "..." if len(comment.content) > 200 else comment.content
        summary += f"\n{i}. **{expert_name}** ({expert_role}) provided input regarding the issue.\n"

    summary += """
### Next Steps
To enable full AI-powered summaries:
1. Set the LLM_PROVIDER environment variable (openai, anthropic, or ollama)
2. Set the LLM_API_KEY environment variable with your API key
3. Optionally set LLM_MODEL to specify the model

### Clarifying Questions
- All experts: Can you elaborate on the root cause of this issue?
- All experts: What are the potential risks of each proposed solution?
- All experts: What timeline do you recommend for implementation?
"""
    return summary
