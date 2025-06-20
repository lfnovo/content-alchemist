# Chapter 9: Complex Workflows - Conditional Execution

## Introduction

Real-world workflows often need to make decisions based on intermediate results, handle different scenarios, or adapt their behavior dynamically. This chapter explores conditional execution, branching logic, Human-in-the-Loop patterns, and building adaptive workflows that respond intelligently to their environment.

## Prerequisites

- Completed Chapters 1-8
- Understanding of workflow state management
- Familiarity with Jinja2 conditional expressions
- Knowledge of edge definitions and workflow control

## What You'll Learn

- Implementing conditional edges and branching logic
- Creating decision trees in workflows
- Using HITL (Human-in-the-Loop) patterns effectively
- Building adaptive workflows that respond to results
- Implementing robust error recovery mechanisms
- Creating self-modifying workflows
- Advanced state management techniques

## The Recipe

Let's create a sophisticated content quality assessment workflow using imports and @references.

First, create the shared model definitions in `models/content_models.yaml`:

```yaml
# models/content_models.yaml
models:
  content_analyzer:
    provider: openai
    model: gpt-4o-mini
    temperature: 0.2
    
  content_enhancer:
    provider: anthropic
    model: claude-3-5-sonnet-20241022
    temperature: 0.6
    
  quality_assessor:
    provider: openai
    model: gpt-4o
    temperature: 0.1
```

Now the main recipe file:

```yaml
# recipes/adaptive_content_quality.yaml
imports:
  - path: "models/content_models.yaml"
    namespace: "content"

recipe:
  name: Adaptive Content Quality Workflow
  version: "1.0"
  
  user_inputs:
    - id: content_topic
      label: "Content topic"
      type: string
      default: "The future of sustainable energy"
      
    - id: target_audience
      label: "Target audience"
      type: literal
      literal_values: ["General Public", "Technical Experts", "Business Leaders", "Students"]
      default: "General Public"
      
    - id: quality_threshold
      label: "Minimum quality score (1-10)"
      type: literal
      literal_values: ["6", "7", "8", "9"]
      default: "7"
      
    - id: max_iterations
      label: "Maximum improvement iterations"
      type: literal
      literal_values: ["1", "2", "3", "5"]
      default: "3"
      
    - id: enable_human_review
      label: "Enable human review for borderline content?"
      type: bool
      default: false
  
  nodes:
    # Step 1: Generate initial content
    - id: generate_initial_content
      type: language_task
      model: "@reference(content.models.content_analyzer)"
      prompt: |
        Create comprehensive content about {{content_topic}} for {{target_audience}}.
        
        {% if target_audience == "General Public" %}
        Use accessible language, relatable examples, and clear explanations.
        {% elif target_audience == "Technical Experts" %}
        Include technical details, data, and industry-specific terminology.
        {% elif target_audience == "Business Leaders" %}
        Focus on strategic implications, ROI, and business impact.
        {% elif target_audience == "Students" %}
        Use educational tone with learning objectives and practical examples.
        {% endif %}
        
        The content should be informative, engaging, and well-structured.
        Aim for 800-1200 words.
      output: initial_content
    
    # Step 2: Assess content quality
    - id: assess_quality
      type: language_task
      model: "@reference(content.models.quality_assessor)"
      prompt: |
        Assess the quality of this content on a scale of 1-10.
        
        Content Topic: {{content_topic}}
        Target Audience: {{target_audience}}
        
        Content to Assess:
        {{initial_content}}
        
        Evaluation Criteria:
        - Clarity and readability (1-10)
        - Accuracy and depth (1-10)
        - Audience appropriateness (1-10)
        - Structure and flow (1-10)
        - Engagement factor (1-10)
        
        Provide your assessment in this exact format:
        
        OVERALL_SCORE: [number from 1-10]
        
        DETAILED_SCORES:
        - Clarity: [score]/10
        - Accuracy: [score]/10
        - Audience: [score]/10
        - Structure: [score]/10
        - Engagement: [score]/10
        
        STRENGTHS:
        - [List key strengths]
        
        IMPROVEMENT_AREAS:
        - [List specific areas needing improvement]
        
        RECOMMENDATION: [APPROVE/ENHANCE/REJECT]
      output: quality_assessment
    
    # Step 3: Parse quality score for decision making
    - id: parse_quality_score
      type: function_task
      function_identifier: "extract_quality_metrics"
      input:
        assessment_text: "{{quality_assessment}}"
        threshold: "{{quality_threshold}}"
      output: quality_metrics
    
    # Step 4: Human review decision point (conditional)
    - id: human_review_check
      type: hitl
      input:
        content: "{{initial_content}}"
        quality_assessment: "{{quality_assessment}}"
        requires_review: "{{quality_metrics.borderline_case}}"
      output: human_feedback
      # This node only executes if human review is enabled and score is borderline
    
    # Step 5: Content enhancement (conditional)
    - id: enhance_content
      type: language_task
      model: "@reference(content.models.content_enhancer)"
      prompt: |
        Enhance this content based on the quality assessment feedback.
        
        Original Content:
        {{initial_content}}
        
        Quality Assessment:
        {{quality_assessment}}
        
        {% if human_feedback and human_feedback.comments %}
        Human Reviewer Feedback:
        {{human_feedback.comments}}
        {% endif %}
        
        Current Quality Score: {{quality_metrics.overall_score}}/10
        Target Quality Score: {{quality_threshold}}/10
        
        Focus on improving:
        {% for area in quality_metrics.improvement_areas %}
        - {{area}}
        {% endfor %}
        
        Provide enhanced content that addresses these specific concerns while maintaining the original intent and target audience appropriateness.
      output: enhanced_content
    
    # Step 6: Re-assess enhanced content
    - id: reassess_quality
      type: language_task
      model: "@reference(content.models.quality_assessor)"
      prompt: |
        Re-assess the quality of this enhanced content using the same criteria as before.
        
        Enhanced Content:
        {% if enhanced_content %}{{enhanced_content}}{% else %}{{initial_content}}{% endif %}
        
        Previous Quality Score: {{quality_metrics.overall_score}}/10
        
        Use the same assessment format as before and compare with the previous version.
        Note any improvements or areas that still need work.
      output: reassessment
    
    # Step 7: Final quality check and iteration decision
    - id: final_quality_check
      type: function_task
      function_identifier: "evaluate_improvement_cycle"
      input:
        original_content: "{{initial_content}}"
        enhanced_content: "{{enhanced_content}}"
        initial_assessment: "{{quality_assessment}}"
        reassessment: "{{reassessment}}"
        current_iteration: 1
        max_iterations: "{{max_iterations}}"
        target_threshold: "{{quality_threshold}}"
      output: cycle_decision
    
    # Step 8: Iterative enhancement loop (conditional)
    - id: iterative_enhancement
      type: language_task
      model: "@reference(content.models.content_enhancer)"
      prompt: |
        This is iteration {{cycle_decision.current_iteration}} of {{max_iterations}}.
        
        Continue enhancing the content based on the latest assessment:
        
        Current Content:
        {{cycle_decision.current_best_content}}
        
        Latest Assessment:
        {{reassessment}}
        
        Remaining Issues:
        {% for issue in cycle_decision.remaining_issues %}
        - {{issue}}
        {% endfor %}
        
        Target Score: {{quality_threshold}}/10
        Current Score: {{cycle_decision.current_score}}/10
        
        Focus on the most critical improvements that will have the highest impact on quality.
      output: iteration_result
    
    # Step 9: Finalization
    - id: finalize_content
      type: function_task
      function_identifier: "prepare_final_output"
      input:
        original_content: "{{initial_content}}"
        enhanced_content: "{{enhanced_content}}"
        iteration_result: "{{iteration_result}}"
        quality_metrics: "{{quality_metrics}}"
        cycle_decision: "{{cycle_decision}}"
        human_feedback: "{{human_feedback}}"
      output: final_package
  
  # Complex edge definitions for conditional flow
  edges:
    # Linear flow to initial assessment
    - from: START
      to: generate_initial_content
    - from: generate_initial_content
      to: assess_quality
    - from: assess_quality
      to: parse_quality_score
    
    # Conditional human review
    - from: parse_quality_score
      to: human_review_check
      condition: "{{enable_human_review == true and quality_metrics.borderline_case == true}}"
    
    # Direct to enhancement if no human review needed
    - from: parse_quality_score
      to: enhance_content
      condition: "{{quality_metrics.needs_enhancement == true and not (enable_human_review == true and quality_metrics.borderline_case == true)}}"
    
    # From human review to enhancement
    - from: human_review_check
      to: enhance_content
      condition: "{{human_feedback.approve_enhancement == true}}"
    
    # Skip enhancement if quality is already sufficient
    - from: parse_quality_score
      to: finalize_content
      condition: "{{quality_metrics.meets_threshold == true}}"
    
    # From human review directly to finalization if approved
    - from: human_review_check
      to: finalize_content
      condition: "{{human_feedback.approve_content == true}}"
    
    # Enhancement flow
    - from: enhance_content
      to: reassess_quality
    - from: reassess_quality
      to: final_quality_check
    
    # Iteration decision
    - from: final_quality_check
      to: iterative_enhancement
      condition: "{{cycle_decision.continue_iterations == true}}"
    
    # Finalization paths
    - from: final_quality_check
      to: finalize_content
      condition: "{{cycle_decision.finalize == true}}"
    
    - from: iterative_enhancement
      to: final_quality_check
      # This creates a loop back for additional iterations
    
    # All paths lead to END
    - from: finalize_content
      to: END
  
  final_outputs:
    - id: final_content
      value: "{{final_package.content}}"
    - id: quality_journey
      value: "{{final_package.quality_progression}}"
    - id: improvement_summary
      value: "{{final_package.improvement_summary}}"
    - id: process_metadata
      value: "{{final_package.metadata}}"
```

## Step-by-Step Breakdown

### 1. Quality Assessment Function

```python
async def extract_quality_metrics(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract structured quality metrics from assessment text."""
    assessment_text = inputs.get("assessment_text", "")
    threshold = int(inputs.get("threshold", 7))
    
    # Parse the overall score
    overall_score = 5  # default
    for line in assessment_text.split('\n'):
        if 'OVERALL_SCORE:' in line:
            try:
                overall_score = int(line.split(':')[1].strip())
            except:
                pass
    
    # Parse recommendation
    recommendation = "ENHANCE"  # default
    for line in assessment_text.split('\n'):
        if 'RECOMMENDATION:' in line:
            recommendation = line.split(':')[1].strip()
    
    # Extract improvement areas
    improvement_areas = []
    in_improvements = False
    for line in assessment_text.split('\n'):
        if 'IMPROVEMENT_AREAS:' in line:
            in_improvements = True
            continue
        elif in_improvements and line.strip().startswith('-'):
            improvement_areas.append(line.strip()[1:].strip())
        elif in_improvements and line.strip() and not line.strip().startswith('-'):
            break
    
    # Calculate decision flags
    meets_threshold = overall_score >= threshold
    needs_enhancement = overall_score < threshold
    borderline_case = abs(overall_score - threshold) <= 1  # Within 1 point of threshold
    
    return {
        "overall_score": overall_score,
        "recommendation": recommendation,
        "improvement_areas": improvement_areas,
        "meets_threshold": meets_threshold,
        "needs_enhancement": needs_enhancement,
        "borderline_case": borderline_case,
        "score_gap": threshold - overall_score
    }
```

### 2. Conditional Edges with Shared Logic

Create shared conditional logic in `conditions/quality_conditions.yaml`:

```yaml
# conditions/quality_conditions.yaml
conditions:
  human_review_needed: "{{enable_human_review == true and quality_metrics.borderline_case == true}}"
  quality_sufficient: "{{quality_metrics.meets_threshold == true}}"
  needs_enhancement: "{{quality_metrics.needs_enhancement == true and not (enable_human_review == true and quality_metrics.borderline_case == true)}}"
  approve_enhancement: "{{human_feedback.approve_enhancement == true}}"
  continue_iterations: "{{cycle_decision.continue_iterations == true}}"
  finalize_workflow: "{{cycle_decision.finalize == true}}"
```

Then import and reference in your main recipe:

```yaml
imports:
  - path: "models/content_models.yaml"
    namespace: "content"
  - path: "conditions/quality_conditions.yaml"
    namespace: "cond"

# Use in edges:
edges:
  # Conditional human review
  - from: parse_quality_score
    to: human_review_check
    condition: "@reference(cond.conditions.human_review_needed)"
  
  # Skip enhancement if quality is sufficient
  - from: parse_quality_score
    to: finalize_content
    condition: "@reference(cond.conditions.quality_sufficient)"
```

Conditional edges with @references enable reusable logic and consistent decision-making across workflows.

### 3. Human-in-the-Loop (HITL) Node

```yaml
- id: human_review_check
  type: hitl
  input:
    content: "{{initial_content}}"
    quality_assessment: "{{quality_assessment}}"
    requires_review: "{{quality_metrics.borderline_case}}"
  output: human_feedback
```

The HITL node pauses execution for human input. In practice, this would present the content and assessment to a human reviewer.

### 4. Iteration Control Function

```python
async def evaluate_improvement_cycle(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate whether to continue improvement iterations."""
    current_iteration = inputs.get("current_iteration", 1)
    max_iterations = int(inputs.get("max_iterations", 3))
    target_threshold = int(inputs.get("target_threshold", 7))
    
    # Parse reassessment for new score
    reassessment = inputs.get("reassessment", "")
    new_score = 5  # default
    for line in reassessment.split('\n'):
        if 'OVERALL_SCORE:' in line:
            try:
                new_score = int(line.split(':')[1].strip())
            except:
                pass
    
    # Determine best content so far
    enhanced_content = inputs.get("enhanced_content")
    original_content = inputs.get("original_content")
    current_best_content = enhanced_content if enhanced_content else original_content
    
    # Decision logic
    meets_threshold = new_score >= target_threshold
    can_continue = current_iteration < max_iterations
    should_continue = not meets_threshold and can_continue
    
    # Extract remaining issues
    remaining_issues = []
    if not meets_threshold:
        in_improvements = False
        for line in reassessment.split('\n'):
            if 'IMPROVEMENT_AREAS:' in line:
                in_improvements = True
                continue
            elif in_improvements and line.strip().startswith('-'):
                remaining_issues.append(line.strip()[1:].strip())
    
    return {
        "continue_iterations": should_continue,
        "finalize": not should_continue,
        "current_iteration": current_iteration + 1,
        "current_score": new_score,
        "target_reached": meets_threshold,
        "iterations_remaining": max_iterations - current_iteration,
        "current_best_content": current_best_content,
        "remaining_issues": remaining_issues
    }
```

### 5. Finalization Function

```python
async def prepare_final_output(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare comprehensive final output package."""
    original_content = inputs.get("original_content")
    enhanced_content = inputs.get("enhanced_content")
    iteration_result = inputs.get("iteration_result")
    quality_metrics = inputs.get("quality_metrics", {})
    cycle_decision = inputs.get("cycle_decision", {})
    human_feedback = inputs.get("human_feedback")
    
    # Determine final content
    final_content = iteration_result or enhanced_content or original_content
    
    # Build quality progression
    quality_progression = {
        "initial_score": quality_metrics.get("overall_score", 0),
        "final_score": cycle_decision.get("current_score", 0),
        "improvement": cycle_decision.get("current_score", 0) - quality_metrics.get("overall_score", 0),
        "threshold_met": cycle_decision.get("target_reached", False),
        "iterations_used": cycle_decision.get("current_iteration", 1) - 1
    }
    
    # Create improvement summary
    improvement_summary = f"""
Content Enhancement Summary:
- Initial Quality Score: {quality_progression['initial_score']}/10
- Final Quality Score: {quality_progression['final_score']}/10
- Improvement: +{quality_progression['improvement']} points
- Iterations Used: {quality_progression['iterations_used']}
- Target Achieved: {'Yes' if quality_progression['threshold_met'] else 'No'}
"""
    
    if human_feedback:
        improvement_summary += f"\n- Human Review: Conducted"
    
    # Metadata
    metadata = {
        "workflow_completion": datetime.now().isoformat(),
        "enhancement_path": "enhanced" if enhanced_content else "original",
        "human_involvement": bool(human_feedback),
        "quality_metrics": quality_metrics,
        "final_decision": cycle_decision
    }
    
    return {
        "content": final_content,
        "quality_progression": quality_progression,
        "improvement_summary": improvement_summary,
        "metadata": metadata
    }
```

## Running Your Recipe

```python
from content_composer import parse_recipe, execute_workflow
import asyncio

async def run_adaptive_content_workflow():
    # Load the recipe
    recipe = parse_recipe("recipes/adaptive_content_quality.yaml")
    
    # Define inputs
    user_inputs = {
        "content_topic": "The role of artificial intelligence in climate change mitigation",
        "target_audience": "Business Leaders",
        "quality_threshold": "8",
        "max_iterations": "3",
        "enable_human_review": True
    }
    
    # Execute the workflow
    print("Starting adaptive content quality workflow...")
    result = await execute_workflow(recipe, user_inputs)
    
    # Access outputs
    final_content = result.get("final_content")
    quality_journey = result.get("quality_journey")
    improvement_summary = result.get("improvement_summary")
    process_metadata = result.get("process_metadata")
    
    print("Adaptive Workflow Complete")
    print("=" * 50)
    print(improvement_summary)
    
    print(f"\nQuality Journey:")
    print(f"Initial Score: {quality_journey['initial_score']}/10")
    print(f"Final Score: {quality_journey['final_score']}/10")
    print(f"Improvement: +{quality_journey['improvement']} points")
    print(f"Target Achieved: {quality_journey['threshold_met']}")
    
    print("\nFinal Content:")
    print("-" * 50)
    print(final_content[:500] + "..." if len(final_content) > 500 else final_content)
    
    return result

if __name__ == "__main__":
    asyncio.run(run_adaptive_content_workflow())
```

## Advanced Conditional Patterns with Shared Definitions

### 1. Multi-Branch Decision Trees with @references

Create reusable decision logic in `conditions/quality_branches.yaml`:

```yaml
# conditions/quality_branches.yaml
quality_thresholds:
  excellent: 9
  good: 7
  fair: 4
  poor: 0

branch_conditions:
  minor_edits: "{{quality_score >= quality_thresholds.good and quality_score < quality_thresholds.excellent}}"
  major_revision: "{{quality_score >= quality_thresholds.fair and quality_score < quality_thresholds.good}}"
  complete_rewrite: "{{quality_score < quality_thresholds.fair}}"
  final_approval: "{{quality_score >= quality_thresholds.excellent}}"
```

Then use in your recipe:

```yaml
imports:
  - path: "conditions/quality_branches.yaml"
    namespace: "branches"

edges:
  # Quality-based branching using shared conditions
  - from: assess_content
    to: minor_edits
    condition: "@reference(branches.branch_conditions.minor_edits)"
    
  - from: assess_content
    to: major_revision
    condition: "@reference(branches.branch_conditions.major_revision)"
    
  - from: assess_content
    to: complete_rewrite
    condition: "@reference(branches.branch_conditions.complete_rewrite)"
    
  - from: assess_content
    to: final_approval
    condition: "@reference(branches.branch_conditions.final_approval)"
```

### 2. State-Based Transitions with Shared Configuration

Create shared state thresholds in `config/feedback_thresholds.yaml`:

```yaml
# config/feedback_thresholds.yaml
feedback_config:
  min_consensus_items: 3
  max_feedback_items: 5
  high_agreement_threshold: 0.8
  low_agreement_threshold: 0.5

state_conditions:
  consensus_reached: "{{feedback_items | length >= feedback_config.min_consensus_items and agreement_score > feedback_config.high_agreement_threshold}}"
  seek_more_input: "{{feedback_items | length < feedback_config.max_feedback_items and agreement_score <= feedback_config.high_agreement_threshold}}"
  escalate_decision: "{{feedback_items | length >= feedback_config.max_feedback_items and agreement_score <= feedback_config.low_agreement_threshold}}"
```

Use with @references:

```yaml
imports:
  - path: "config/feedback_thresholds.yaml"
    namespace: "feedback"

edges:
  # Different paths based on accumulated state
  - from: accumulate_feedback
    to: consensus_reached
    condition: "@reference(feedback.state_conditions.consensus_reached)"
    
  - from: accumulate_feedback
    to: seek_more_input
    condition: "@reference(feedback.state_conditions.seek_more_input)"
    
  - from: accumulate_feedback
    to: escalate_decision
    condition: "@reference(feedback.state_conditions.escalate_decision)"
```

### 3. Time-Based Conditionals with Shared Configuration

Create shared time thresholds in `config/time_constraints.yaml`:

```yaml
# config/time_constraints.yaml
time_thresholds:
  urgent_hours: 24      # Less than 24 hours
  standard_hours: 168   # 1-7 days (168 hours)
  
time_conditions:
  expedited_needed: "{{time_remaining < time_thresholds.urgent_hours}}"
  standard_timeline: "{{time_remaining >= time_thresholds.urgent_hours and time_remaining < time_thresholds.standard_hours}}"
  comprehensive_available: "{{time_remaining >= time_thresholds.standard_hours}}"
```

Use in your recipe:

```yaml
imports:
  - path: "config/time_constraints.yaml"
    namespace: "time"

nodes:
  - id: check_deadline
    type: function_task
    function_identifier: "evaluate_time_constraints"
    
edges:
  - from: check_deadline
    to: expedited_process
    condition: "@reference(time.time_conditions.expedited_needed)"
    
  - from: check_deadline
    to: standard_process
    condition: "@reference(time.time_conditions.standard_timeline)"
    
  - from: check_deadline
    to: comprehensive_process
    condition: "@reference(time.time_conditions.comprehensive_available)"
```

## Advanced HITL Patterns with Shared Configurations

### 1. Approval Workflows with @references

Create shared approval logic in `workflows/approval_patterns.yaml`:

```yaml
# workflows/approval_patterns.yaml
approval_roles:
  manager:
    escalation_authority: true
    approval_limit: "standard"
  director:
    escalation_authority: true
    approval_limit: "high"
  ceo:
    escalation_authority: false
    approval_limit: "unlimited"

approval_conditions:
  escalate_to_director: "{{manager_decision.escalate == true}}"
  implement_approved: "{{manager_decision.approved == true}}"
  needs_revision: "{{manager_decision.needs_revision == true}}"
  director_final_approval: "{{director_decision.approved == true}}"
```

Use in your workflow:

```yaml
imports:
  - path: "workflows/approval_patterns.yaml"
    namespace: "approval"

nodes:
  - id: manager_review
    type: hitl
    input:
      document: "{{draft_document}}"
      approval_level: "@reference(approval.approval_roles.manager)"
    output: manager_decision

edges:
  - from: manager_review
    to: director_review
    condition: "@reference(approval.approval_conditions.escalate_to_director)"
    
  - from: manager_review
    to: implement_changes
    condition: "@reference(approval.approval_conditions.implement_approved)"
    
  - from: manager_review
    to: revise_document
    condition: "@reference(approval.approval_conditions.needs_revision)"
```

### 2. Collaborative Review with Shared Stakeholder Definitions

Create shared stakeholder configurations in `config/stakeholder_roles.yaml`:

```yaml
# config/stakeholder_roles.yaml
stakeholder_types:
  technical:
    role: "Technical Reviewer"
    expertise: ["architecture", "implementation", "security"]
    weight: 0.3
  business:
    role: "Business Analyst"
    expertise: ["requirements", "user_experience", "roi"]
    weight: 0.4
  legal:
    role: "Legal Counsel"
    expertise: ["compliance", "contracts", "risk"]
    weight: 0.3

review_templates:
  hitl_input:
    document: "{{proposal}}"
    reviewer_role: "{{item.role}}"
    focus_areas: "{{item.expertise}}"
    review_weight: "{{item.weight}}"
```

Use with @references:

```yaml
imports:
  - path: "config/stakeholder_roles.yaml"
    namespace: "stakeholders"

nodes:
  - id: gather_stakeholder_input
    type: map
    over: stakeholder_list
    task:
      type: hitl
      input: "@reference(stakeholders.review_templates.hitl_input)"
      output: stakeholder_feedback

  - id: synthesize_feedback
    type: function_task
    function_identifier: "consolidate_stakeholder_input"
    input:
      feedback_collection: "{{gather_stakeholder_input}}"
      stakeholder_weights: "@reference(stakeholders.stakeholder_types)"
```

### 3. Progressive Enhancement

```yaml
- id: iterative_review
  type: hitl
  input:
    content: "{{current_version}}"
    iteration_number: "{{current_iteration}}"
    previous_feedback: "{{accumulated_feedback}}"
  output: iteration_feedback

edges:
  - from: iterative_review
    to: apply_feedback
    condition: "{{iteration_feedback.continue_improving == true}}"
    
  - from: iterative_review
    to: finalize_content
    condition: "{{iteration_feedback.ready_to_publish == true}}"
```

## Error Recovery Mechanisms with Shared Recovery Patterns

### 1. Fallback Strategies with @references

Create shared recovery logic in `patterns/error_recovery.yaml`:

```yaml
# patterns/error_recovery.yaml
recovery_conditions:
  primary_success: "{{primary_analysis.success == true}}"
  primary_failed: "{{primary_analysis.success == false}}"
  backup_success: "{{backup_analysis.success == true}}"
  backup_failed: "{{backup_analysis.success == false}}"
  
recovery_paths:
  use_primary: "primary_success"
  try_backup: "primary_failed"
  backup_succeeded: "backup_success"
  escalate_manual: "backup_failed"

error_handling:
  max_retries: 3
  backoff_multiplier: 2
  timeout_seconds: 30
```

Use in your workflow:

```yaml
imports:
  - path: "patterns/error_recovery.yaml"
    namespace: "recovery"

edges:
  # Primary path
  - from: primary_analysis
    to: synthesize_results
    condition: "@reference(recovery.recovery_conditions.primary_success)"
    
  # Fallback path
  - from: primary_analysis
    to: backup_analysis
    condition: "@reference(recovery.recovery_conditions.primary_failed)"
    
  - from: backup_analysis
    to: synthesize_results
    condition: "@reference(recovery.recovery_conditions.backup_success)"
    
  # Emergency path
  - from: backup_analysis
    to: manual_intervention
    condition: "@reference(recovery.recovery_conditions.backup_failed)"
```

### 2. Retry Logic

```python
async def implement_retry_logic(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Implement intelligent retry with exponential backoff."""
    attempt = inputs.get("attempt", 1)
    max_attempts = inputs.get("max_attempts", 3)
    last_error = inputs.get("last_error")
    
    if attempt > max_attempts:
        return {
            "should_retry": False,
            "escalate": True,
            "final_error": last_error
        }
    
    # Exponential backoff
    wait_time = 2 ** (attempt - 1)
    
    # Error analysis
    if "rate_limit" in str(last_error).lower():
        wait_time *= 2  # Longer wait for rate limits
    
    return {
        "should_retry": True,
        "wait_time": wait_time,
        "next_attempt": attempt + 1,
        "retry_strategy": "exponential_backoff"
    }
```

### 3. Circuit Breaker Pattern with Shared Service Configuration

Create shared service health logic in `config/service_health.yaml`:

```yaml
# config/service_health.yaml
service_thresholds:
  healthy_response_time: 1000  # milliseconds
  degraded_response_time: 5000
  error_rate_threshold: 0.05   # 5%
  
health_conditions:
  service_healthy: "{{service_status.healthy == true}}"
  service_degraded: "{{service_status.degraded == true}}"
  service_unavailable: "{{service_status.unavailable == true}}"
  
circuit_breaker:
  failure_threshold: 5
  recovery_timeout: 60  # seconds
  half_open_max_calls: 3
```

Use with @references:

```yaml
imports:
  - path: "config/service_health.yaml"
    namespace: "health"

nodes:
  - id: check_service_health
    type: function_task
    function_identifier: "evaluate_service_status"
    input:
      thresholds: "@reference(health.service_thresholds)"
      circuit_config: "@reference(health.circuit_breaker)"
      
edges:
  - from: check_service_health
    to: use_primary_service
    condition: "@reference(health.health_conditions.service_healthy)"
    
  - from: check_service_health
    to: use_backup_service
    condition: "@reference(health.health_conditions.service_degraded)"
    
  - from: check_service_health
    to: offline_mode
    condition: "@reference(health.health_conditions.service_unavailable)"
```

## Hands-On Exercise

### Exercise 1: Document Approval Workflow with @references

Create shared approval configuration in `config/document_approval.yaml`:

```yaml
# config/document_approval.yaml
review_types:
  author_final_check:
    reviewer_role: "author"
    required_checks: ["grammar", "completeness", "accuracy"]
  manager_approval:
    reviewer_role: "manager"
    required_checks: ["business_alignment", "resource_impact"]
  legal_compliance:
    reviewer_role: "legal"
    required_checks: ["compliance", "risk_assessment", "liability"]

approval_conditions:
  author_approved: "{{author_review.approved == true}}"
  manager_approved: "{{manager_approval.approved == true}}"
  needs_legal_review: "{{manager_approval.approved == true and document_type == 'contract'}}"
  ready_to_publish: "{{manager_approval.approved == true and document_type != 'contract'}}"

document_types:
  contract:
    requires_legal: true
    approval_levels: ["author", "manager", "legal"]
  policy:
    requires_legal: false
    approval_levels: ["author", "manager"]
```

Create the workflow using @references:

```yaml
# exercises/document_approval_workflow.yaml
imports:
  - path: "models/content_models.yaml"
    namespace: "content"
  - path: "config/document_approval.yaml"
    namespace: "approval"

nodes:
  - id: draft_document
    type: language_task
    model: "@reference(content.models.content_analyzer)"
    
  - id: author_review
    type: hitl
    input:
      document: "{{draft_document}}"
      review_config: "@reference(approval.review_types.author_final_check)"
      
  - id: manager_approval
    type: hitl
    input:
      document: "{{draft_document}}"
      review_config: "@reference(approval.review_types.manager_approval)"
      
  - id: legal_review
    type: hitl
    input:
      document: "{{draft_document}}"
      review_config: "@reference(approval.review_types.legal_compliance)"

edges:
  - from: author_review
    to: manager_approval
    condition: "@reference(approval.approval_conditions.author_approved)"
    
  - from: manager_approval
    to: legal_review
    condition: "@reference(approval.approval_conditions.needs_legal_review)"
    
  - from: manager_approval
    to: publish_document
    condition: "@reference(approval.approval_conditions.ready_to_publish)"
```

### Exercise 2: Adaptive Learning Workflow with @references

Create shared learning configurations in `config/learning_paths.yaml`:

```yaml
# config/learning_paths.yaml
learning_levels:
  beginner:
    content_complexity: "basic"
    examples_needed: 5
    explanation_depth: "detailed"
  intermediate:
    content_complexity: "moderate"
    examples_needed: 3
    explanation_depth: "standard"
  advanced:
    content_complexity: "complex"
    examples_needed: 1
    explanation_depth: "concise"

path_conditions:
  route_beginner: "{{user_level.expertise == 'beginner'}}"
  route_intermediate: "{{user_level.expertise == 'intermediate'}}"
  route_advanced: "{{user_level.expertise == 'advanced'}}"

content_templates:
  beginner_prompt: "Create {{content_type}} content for beginners with {{learning_levels.beginner.examples_needed}} examples and {{learning_levels.beginner.explanation_depth}} explanations."
  intermediate_prompt: "Create {{content_type}} content for intermediate learners with {{learning_levels.intermediate.examples_needed}} examples."
  advanced_prompt: "Create {{content_type}} content for advanced users with {{learning_levels.advanced.examples_needed}} example."
```

Use in the adaptive workflow:

```yaml
# exercises/adaptive_learning_workflow.yaml
imports:
  - path: "config/learning_paths.yaml"
    namespace: "learning"
  - path: "models/content_models.yaml"
    namespace: "content"

nodes:
  - id: assess_user_level
    type: function_task
    function_identifier: "evaluate_user_expertise"
    input:
      learning_config: "@reference(learning.learning_levels)"
      
  - id: beginner_content
    type: language_task
    model: "@reference(content.models.content_analyzer)"
    prompt: "@reference(learning.content_templates.beginner_prompt)"
    
  - id: intermediate_content
    type: language_task
    model: "@reference(content.models.content_analyzer)"
    prompt: "@reference(learning.content_templates.intermediate_prompt)"
    
  - id: advanced_content
    type: language_task
    model: "@reference(content.models.content_enhancer)"
    prompt: "@reference(learning.content_templates.advanced_prompt)"
      
edges:
  - from: assess_user_level
    to: beginner_content
    condition: "@reference(learning.path_conditions.route_beginner)"
    
  - from: assess_user_level
    to: intermediate_content
    condition: "@reference(learning.path_conditions.route_intermediate)"
    
  - from: assess_user_level
    to: advanced_content
    condition: "@reference(learning.path_conditions.route_advanced)"
```

### Exercise 3: Quality Gate Workflow with @references

Create shared quality standards in `config/quality_gates.yaml`:

```yaml
# config/quality_gates.yaml
quality_standards:
  minimum_coverage: 80
  maximum_bugs: 0
  maximum_vulnerabilities: 0
  performance_threshold: 2000  # milliseconds
  
gate_conditions:
  deployment_ready: "{{quality_metrics.coverage >= quality_standards.minimum_coverage and quality_metrics.bugs <= quality_standards.maximum_bugs}}"
  needs_fixes: "{{quality_metrics.coverage < quality_standards.minimum_coverage or quality_metrics.bugs > quality_standards.maximum_bugs}}"
  security_passed: "{{quality_metrics.vulnerabilities <= quality_standards.maximum_vulnerabilities}}"
  performance_passed: "{{quality_metrics.response_time <= quality_standards.performance_threshold}}"

test_configurations:
  unit_tests:
    timeout: 300
    parallel: true
    coverage_required: true
  integration_tests:
    timeout: 600
    parallel: false
    coverage_required: false
  security_scan:
    timeout: 900
    fail_on_medium: true
```

Use in the quality gate workflow:

```yaml
# exercises/quality_gate_workflow.yaml
imports:
  - path: "config/quality_gates.yaml"
    namespace: "quality"

nodes:
  - id: run_tests
    type: function_task
    function_identifier: "execute_test_suite"
    input:
      test_config: "@reference(quality.test_configurations)"
      quality_standards: "@reference(quality.quality_standards)"
    
  - id: quality_gate
    type: function_task
    function_identifier: "evaluate_quality_metrics"
    input:
      standards: "@reference(quality.quality_standards)"
    
  - id: security_scan
    type: function_task
    function_identifier: "run_security_analysis"
    input:
      scan_config: "@reference(quality.test_configurations.security_scan)"
      
edges:
  - from: quality_gate
    to: security_scan
    condition: "@reference(quality.gate_conditions.deployment_ready)"
    
  - from: security_scan
    to: deploy_to_staging
    condition: "@reference(quality.gate_conditions.security_passed)"
    
  - from: quality_gate
    to: fix_issues
    condition: "@reference(quality.gate_conditions.needs_fixes)"
    
  - from: fix_issues
    to: run_tests
    # Creates feedback loop for continuous improvement
```

## Common Pitfalls with @references

1. **Overly Complex Conditions**: Use @references to break complex logic into manageable parts
   ```yaml
   # Instead of complex inline conditions
   condition: "{{(score >= 8 and feedback.positive) or (score >= 7 and iterations < 3 and user_type == 'premium')}}"
   
   # Create shared condition logic
   # conditions/complex_approval.yaml
   approval_logic:
     high_score_positive: "{{score >= 8 and feedback.positive}}"
     medium_score_premium: "{{score >= 7 and iterations < 3 and user_type == 'premium'}}"
     final_approval: "{{approval_logic.high_score_positive or approval_logic.medium_score_premium}}"
   
   # Use clean reference
   condition: "@reference(approval.approval_logic.final_approval)"
   ```

2. **Infinite Loops**: Share iteration limits across workflows
   ```yaml
   # config/iteration_limits.yaml
   loop_controls:
     max_iterations: 5
     improvement_threshold: 0.1
     
   safe_conditions:
     continue_iterating: "{{needs_improvement == true and iterations < loop_controls.max_iterations}}"
   
   # Use in workflow
   condition: "@reference(limits.safe_conditions.continue_iterating)"
   ```

3. **State Dependencies**: Create defensive conditions with @references
   ```yaml
   # conditions/safe_state_checks.yaml
   state_validations:
     quality_exists: "{{quality_assessment is defined}}"
     score_available: "{{quality_assessment.score is defined}}"
     safe_quality_check: "{{state_validations.quality_exists and state_validations.score_available and quality_assessment.score >= 7}}"
   
   # Use defensive condition
   condition: "@reference(safety.state_validations.safe_quality_check)"
   ```

4. **HITL Configuration**: Share timeout and fallback settings
   ```yaml
   # config/hitl_settings.yaml
   hitl_config:
     default_timeout: 3600  # 1 hour
     fallback_action: "approve"
     escalation_timeout: 7200  # 2 hours
     
   timeout_conditions:
     standard_timeout: "{{time_elapsed > hitl_config.default_timeout}}"
     escalation_needed: "{{time_elapsed > hitl_config.escalation_timeout}}"
   ```

## Key Takeaways

- Conditional edges with @references enable intelligent, reusable workflow branching
- HITL nodes with shared configurations standardize human decision-making patterns
- State-based conditions using imports create adaptive, maintainable workflows
- Error recovery mechanisms with @references ensure consistent, robust execution across workflows
- Complex conditions should be broken into shared, readable components using imports and @references
- Always include exit conditions in shared logic to prevent infinite loops across all workflows
- @references enable testing conditional paths once and reusing them everywhere
- Shared condition libraries make workflows more maintainable and less error-prone
- Import namespaces organize complex conditional logic hierarchically
- Conditional logic becomes documentation when properly structured with @references

## Next Steps

In Chapter 10, we'll build the most complex workflow yet - a complete podcast production pipeline that demonstrates all the concepts learned, including:
- End-to-end content production
- Complex audio processing
- Multi-stage quality control
- Advanced voice mapping
- Production optimization techniques

Ready for the final challenge? Continue to Chapter 10!

<function_calls>
<invoke name="TodoWrite">
<parameter name="todos">[{"id": "chapter07", "content": "Create Chapter 7: Map-Reduce Pattern - Processing Collections", "status": "completed", "priority": "high"}, {"id": "chapter08", "content": "Create Chapter 8: Advanced Orchestration - Mix of Agents", "status": "completed", "priority": "high"}, {"id": "chapter09", "content": "Create Chapter 9: Complex Workflows - Conditional Execution", "status": "completed", "priority": "high"}, {"id": "chapter10", "content": "Create Chapter 10: Production Pipeline - The Full Podcast", "status": "in_progress", "priority": "high"}, {"id": "appendices", "content": "Create all appendices (A-E) as referenced in the index", "status": "pending", "priority": "medium"}]