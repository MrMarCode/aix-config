---
description: lessons-learned
auto_execution_mode: 1
---

# Conduct a retrospective analysis of this conversation

Perform a comprehensive retrospective of our conversation to identify what went well,
what didn't, and what can be learned for future interactions.

## Step 1: Review the Conversation

Carefully review the entire conversation from start to finish. Identify:
   * All tasks and requests made by the user
   * All code changes, file modifications, and decisions you made
   * Points where the user corrected you or changed your approach
   * Areas where the conversation flowed smoothly vs areas with friction

## Step 2: Analyze Code Changes

Use git diff to examine changes made after your modifications:
   * Check git status and git diff to see what the user changed after you made edits
   * Look at the file history in claude/file-history/ to see patterns of user
     modifications
   * Pay special attention to code you wrote that the user later modified - these
     changes reveal what the user values

For each user modification, ask yourself:
   * What did I write originally?
   * How did the user change it?
   * What does this change reveal about their preferences?
   * What principle or value does this reflect?

## Step 3: Identify Patterns

Look for recurring patterns across multiple changes:
   * Coding style preferences (that aren't already in the rules)
   * Communication style preferences
   * Decision-making priorities
   * Quality vs speed trade-offs
   * Areas where you consistently miss the mark
   * Areas where you consistently deliver value

## Step 4: What Went Well

List specific things that went well:
   * Decisions that aligned with user values
   * Code that wasn't modified or required minimal changes
   * Processes that were efficient and effective
   * Communication that was clear and helpful
   * Areas where you demonstrated understanding of user preferences

For each item, explain WHY it went well in the context of this user's values.

## Step 5: What Didn't Go Well

List specific things that didn't go well:
   * Misunderstandings or misalignments
   * Code that required significant rework
   * Processes that were inefficient
   * Communication that was unclear or unhelpful
   * Areas where you didn't meet expectations

For each item, explain:
   * What went wrong and why
   * What the root cause was (use the Five Whys technique)
   * What should have been done instead

## Step 6: Extract Insights

Based on the patterns and analysis, identify:
   * New rules or preferences that should be added to the user's configuration
   * Existing rules that need clarification or emphasis
   * Principles the user values that aren't yet captured
   * Areas for improvement in future interactions

## Step 7: Actionable Recommendations

Provide specific, actionable recommendations:
   * Suggest new rules to add to ~/.claude/rules/ (with example content)
   * Suggest modifications to existing rules
   * Suggest process improvements
   * Suggest communication improvements

## Format Your Response

Structure your retrospective clearly:

### Summary
Brief overview of the conversation and key outcomes

### What Went Well
- Bullet points with explanations

### What Didn't Go Well
- Bullet points with root cause analysis

### Key Insights
- Patterns and lessons learned
- What the user values based on their modifications

### Recommendations
- Specific actions to take
- Proposed rule additions/changes
- Process improvements

## Important Notes

   * Be honest and critical - the goal is learning, not self-congratulation
   * Focus on patterns, not one-off issues
   * Base insights on evidence (actual changes made), not assumptions
   * Be specific - avoid vague observations
   * Prioritize insights that can lead to concrete rule changes