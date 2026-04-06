export interface CheckMetadata {
  url: string;
  id: string;
  fact_check_metadata: CheckInternalMetadata;
  article_text: string;
  summary: string | null;
  bias_rating: string | null;
  key_points: string[];
  article_metadata: Record<string, any>;
  accuracy_score: number | null;
  completeness_score: number | null;
  accuracy_explanation: string | null;
  completeness_explanation: string | null;
  sources: string[];
  political_bias: string | null;
  sensationalism: string | null;
  emotional_language: string | null;
  political_score: number | null;
  sensationalism_score: number | null;
  emotional_language_score: number | null;
  finished: boolean;
}

export interface CheckInternalMetadata {
  accuracy_agent: AgentMetadata | undefined;
  bias_agent: AgentMetadata | undefined;
  completeness_agent: AgentMetadata | undefined;
  scraper_duration: number | undefined;
  summary_duration: number | undefined;
  agents_duration: number | undefined;
  check_duration_from_start: number | undefined;
  check_duration_from_submitted: number | undefined;
  check_submitted: string;
  check_started: string | undefined;
  check_finished: string | undefined;
}

export interface AgentMetadata {
  started: string | undefined;
  scheduled: string | undefined;
  finished: string | undefined;
  tool_calls: Record<string, number> | undefined;
  total_tool_calls: number | undefined;
}
