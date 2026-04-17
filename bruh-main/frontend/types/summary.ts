export interface PatientInfo {
    name: string;
    age: string;
    gender: string;
}

export interface ClinicalInfo {
    symptoms: string[];
    duration: string;
    severity: string;
    assessment?: string;
    urgency_level?: string;
    reason?: string;
    current_status?: string;
    timeline?: string;
    first_aid?: string[];
    home_care?: string[];
    otc_guidance?: string[];
    when_to_seek_care?: string[];
    possible_causes?: string[];
    medical_reasoning?: string[];
}

export interface ConversationLog {
    role: string;
    content: string;
}

export interface ReportSummary {
    patient: PatientInfo;
    clinical_info: ClinicalInfo;
    conversation_logs: ConversationLog[];
    language: string;
    timestamp: string;
}

export interface GenerateSummaryResponse {
    structured_data: ReportSummary;
    summary_text: string;
}
