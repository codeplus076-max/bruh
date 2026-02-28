export interface PatientInfo {
    name: string;
    age: string;
    gender: string;
}

export interface ClinicalInfo {
    symptoms: string[];
    duration: string;
    severity: string;
    predicted_condition: string;
    confidence: string;
    risk_level: string;
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
