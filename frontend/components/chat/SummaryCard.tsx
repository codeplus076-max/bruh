"use client";

import { useState } from "react";
import { Download, Copy, CheckCircle2, User, Activity, AlertTriangle, FileText, MessageSquare, Brain } from "lucide-react";
import jsPDF from "jspdf";
import html2canvas from "html2canvas";
import { ReportSummary } from "@/types/summary";

interface SummaryCardProps {
    summary: ReportSummary;
    rawText: string;
}

export function SummaryCard({ summary, rawText }: SummaryCardProps) {
    const [copied, setCopied] = useState(false);
    const [isExporting, setIsExporting] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(rawText);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    const handleDownloadPDF = async () => {
        const element = document.getElementById("pdf-report-container");
        if (!element) return;

        setIsExporting(true);
        try {
            // Temporarily make the hidden container visible for canvas capture
            element.style.display = "block";

            const canvas = await html2canvas(element, {
                scale: 2, // High resolution
                useCORS: true,
                logging: false,
                windowWidth: 800 // Force a specific width for consistent rendering
            });

            element.style.display = "none";

            const imgData = canvas.toDataURL("image/jpeg", 1.0);

            const pdf = new jsPDF("p", "mm", "a4");
            const pdfWidth = pdf.internal.pageSize.getWidth();
            const pdfHeight = pdf.internal.pageSize.getHeight();

            const imgWidth = pdfWidth;
            const imgHeight = (canvas.height * imgWidth) / canvas.width;

            let heightLeft = imgHeight;
            let position = 0;

            // Add first page
            pdf.addImage(imgData, "JPEG", 0, position, imgWidth, imgHeight);
            heightLeft -= pdfHeight;

            // Handle multiple pages automatically
            while (heightLeft >= 0) {
                position = heightLeft - imgHeight;
                pdf.addPage();
                pdf.addImage(imgData, "JPEG", 0, position, imgWidth, imgHeight);
                heightLeft -= pdfHeight;
            }

            const fileName = `upchaar_report_${summary.patient.name.replace(/\s+/g, '_')}_${new Date().getTime()}.pdf`;
            pdf.save(fileName);
        } catch (error) {
            console.error("Error generating PDF:", error);
        } finally {
            setIsExporting(false);
        }
    };

    return (
        <div className="bg-surface border border-borderDark rounded-2xl shadow-xl overflow-hidden mt-6 w-full animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* Header */}
            <div className="bg-primary/10 px-6 py-4 flex flex-col sm:flex-row items-center justify-between border-b border-primary/20 gap-4">
                <div className="flex items-center gap-3 w-full sm:w-auto">
                    <div className="p-2 bg-primary/20 rounded-lg text-primary">
                        <FileText className="w-5 h-5" />
                    </div>
                    <div>
                        <h3 className="font-heading font-bold text-textMain text-lg">AI Generated Report</h3>
                        <p className="text-primary text-xs uppercase tracking-wider">Patient Summary Summary</p>
                    </div>
                </div>

                <div className="flex items-center gap-2 w-full sm:w-auto shrink-0">
                    <button
                        onClick={handleCopy}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-surface hover:bg-surfaceHighlight border border-borderDark rounded-xl text-sm font-medium transition-all text-textMain"
                    >
                        {copied ? (
                            <><CheckCircle2 className="w-4 h-4 text-emerald-500" /> Copied</>
                        ) : (
                            <><Copy className="w-4 h-4" /> Copy</>
                        )}
                    </button>
                    <button
                        onClick={handleDownloadPDF}
                        disabled={isExporting}
                        className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-4 py-2 bg-primary text-white rounded-xl text-sm font-medium hover:bg-primary-dark transition-all shadow-neon disabled:opacity-50"
                    >
                        {isExporting ? <span className="w-4 h-4 border-2 border-white/20 border-t-white rounded-full animate-spin" /> : <Download className="w-4 h-4" />}
                        {isExporting ? "Exporting..." : "PDF"}
                    </button>
                </div>
            </div>

            {/* Content Body */}
            <div className="p-6 grid gap-6 sm:grid-cols-2">
                {/* Patient Info Group */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-textMuted text-sm font-bold uppercase tracking-wider border-b border-borderDark pb-2">
                        <User className="w-4 h-4" /> Patient Details
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-surfaceHighlight/50 p-3 rounded-xl border border-borderDark/50">
                            <p className="text-xs text-textMuted mb-1">Name</p>
                            <p className="font-medium text-textMain capitalize">{summary.patient.name}</p>
                        </div>
                        <div className="bg-surfaceHighlight/50 p-3 rounded-xl border border-borderDark/50">
                            <p className="text-xs text-textMuted mb-1">Age</p>
                            <p className="font-medium text-textMain">{summary.patient.age}</p>
                        </div>
                        <div className="bg-surfaceHighlight/50 p-3 rounded-xl border border-borderDark/50 col-span-2">
                            <p className="text-xs text-textMuted mb-1">Gender</p>
                            <p className="font-medium text-textMain capitalize">{summary.patient.gender}</p>
                        </div>
                    </div>
                </div>

                {/* Clinical Info Group */}
                <div className="space-y-4">
                    <div className="flex items-center gap-2 text-textMuted text-sm font-bold uppercase tracking-wider border-b border-borderDark pb-2">
                        <Activity className="w-4 h-4" /> Clinical Info
                    </div>
                    <div className="bg-surfaceHighlight/50 p-3 rounded-xl border border-borderDark/50">
                        <p className="text-xs text-textMuted mb-1">Symptoms</p>
                        <div className="flex flex-wrap gap-1.5 mt-2">
                            {summary.clinical_info.symptoms.map((sym, i) => (
                                <span key={i} className="px-2 py-1 bg-surface border border-borderDark rounded-md text-xs text-textMain capitalize">
                                    {sym}
                                </span>
                            ))}
                        </div>
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div className="bg-surfaceHighlight/50 p-3 rounded-xl border border-borderDark/50">
                            <p className="text-xs text-textMuted mb-1">Duration</p>
                            <p className="font-medium text-textMain capitalize">{summary.clinical_info.duration}</p>
                        </div>
                        <div className="bg-surfaceHighlight/50 p-3 rounded-xl border border-borderDark/50">
                            <p className="text-xs text-textMuted mb-1">Severity</p>
                            <p className="font-medium text-textMain capitalize">{summary.clinical_info.severity}</p>
                        </div>
                    </div>
                </div>

                {/* Prediction Result (Full Width) */}
                <div className="sm:col-span-2 space-y-4">
                    <div className="flex items-center gap-2 text-textMuted text-sm font-bold uppercase tracking-wider border-b border-borderDark pb-2">
                        <AlertTriangle className="w-4 h-4 text-warning" /> AI Prediction
                    </div>
                    <div className={`p-4 rounded-xl border flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 ${summary.clinical_info.risk_level.toLowerCase().includes('high') || summary.clinical_info.risk_level.toLowerCase().includes('emergency')
                        ? 'bg-danger/10 border-danger/30'
                        : 'bg-primary/5 border-primary/20'
                        }`}>
                        <div>
                            <p className="text-sm font-medium text-textMuted">Condition</p>
                            <p className="text-xl font-bold text-textMain mt-1">{summary.clinical_info.predicted_condition}</p>
                            <p className="text-sm text-textMain/80 mt-1">Confidence Score: <span className="font-medium">{summary.clinical_info.confidence}</span></p>
                        </div>
                        <div className={`px-4 py-2 rounded-lg font-bold text-sm tracking-wide ${summary.clinical_info.risk_level.toLowerCase().includes('high') || summary.clinical_info.risk_level.toLowerCase().includes('emergency')
                            ? 'bg-danger text-white'
                            : 'bg-primary text-white'
                            }`}>
                            {summary.clinical_info.risk_level} Risk
                        </div>
                    </div>
                </div>
            </div>

            {/* Footer / Disclaimer */}
            <div className="bg-surfaceHighlight/30 px-6 py-3 border-t border-borderDark flex items-center gap-2">
                <AlertTriangle className="w-3.5 h-3.5 text-textMuted shrink-0" />
                <p className="text-[11px] text-textMuted leading-relaxed">
                    Disclaimer: This summary is AI-generated based on conversation history. It is meant for informational purposes and should not replace professional medical diagnosis, advice, or treatment.
                </p>
            </div>

            {/* HIDDEN IN DOM - USED ONLY FOR HIGH RES PDF EXPORT */}
            <div className="absolute left-[-9999px] top-[-9999px]">
                <div id="pdf-report-container" className="bg-white text-black p-10 w-[800px] font-sans">
                    {/* PDF Header */}
                    <div className="border-b-2 border-primary pb-6 mb-6">
                        <div className="flex justify-between items-start">
                            <div>
                                <h1 className="text-3xl font-black text-primary mb-1">Upchaar AI Diagnostics</h1>
                                <p className="text-gray-500 font-medium">Comprehensive Patient Medical Report</p>
                            </div>
                            <div className="text-right">
                                <p className="text-sm font-bold text-gray-700">Date Generated</p>
                                <p className="text-sm text-gray-500">{new Date().toLocaleString()}</p>
                                <p className="text-xs text-gray-400 mt-1 uppercase tracking-wider">Report Language: {summary.language || "EN"}</p>
                            </div>
                        </div>
                    </div>

                    {/* PDF Patient Details */}
                    <div className="mb-8 p-5 bg-gray-50 rounded-xl border border-gray-100">
                        <h2 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4 flex items-center gap-2">
                            <User className="w-5 h-5 text-primary" /> Patient Profile
                        </h2>
                        <div className="grid grid-cols-3 gap-6">
                            <div>
                                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-1">Full Name</p>
                                <p className="font-bold text-gray-900 text-lg capitalize">{summary.patient.name}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-1">Age</p>
                                <p className="font-bold text-gray-900 text-lg">{summary.patient.age} Yrs</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-1">Gender</p>
                                <p className="font-bold text-gray-900 text-lg capitalize">{summary.patient.gender}</p>
                            </div>
                        </div>
                    </div>

                    {/* PDF Clinical Details */}
                    <div className="mb-8">
                        <h2 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4 flex items-center gap-2">
                            <Activity className="w-5 h-5 text-primary" /> Clinical Presentation
                        </h2>
                        <div className="grid grid-cols-2 gap-6 mb-4">
                            <div>
                                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-1">Condition Duration</p>
                                <p className="font-medium text-gray-900">{summary.clinical_info.duration}</p>
                            </div>
                            <div>
                                <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-1">Reported Severity</p>
                                <p className="font-medium text-gray-900">{summary.clinical_info.severity}</p>
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-gray-500 font-semibold uppercase tracking-wider mb-2">Identified Symptoms</p>
                            <div className="flex flex-wrap gap-2">
                                {summary.clinical_info.symptoms.map((sym, i) => (
                                    <span key={i} className="px-3 py-1.5 bg-primary/10 border border-primary/20 text-primary font-medium rounded-lg text-sm capitalize">
                                        {sym}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>

                    {/* PDF AI Prediction */}
                    <div className="mb-8">
                        <h2 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4 flex items-center gap-2">
                            <AlertTriangle className="w-5 h-5 text-warning" /> AI Triage Assessment
                        </h2>
                        <div className={`p-5 rounded-xl border ${summary.clinical_info.risk_level.toLowerCase().includes('high') ? 'bg-red-50 border-red-200' : 'bg-green-50 border-green-200'}`}>
                            <div className="flex justify-between items-center mb-4">
                                <div>
                                    <p className="text-sm font-semibold text-gray-600 mb-1">Primary Predicted Condition</p>
                                    <p className="text-2xl font-black text-gray-900">{summary.clinical_info.predicted_condition}</p>
                                </div>
                                <div className={`px-4 py-2 rounded-lg font-bold text-lg border bg-white ${summary.clinical_info.risk_level.toLowerCase().includes('high') ? 'text-red-700 border-red-300 shadow-sm' : 'text-green-700 border-green-300 shadow-sm'}`}>
                                    {summary.clinical_info.risk_level} Risk Level
                                </div>
                            </div>
                            <div className="w-full bg-white rounded-full h-3 mb-2 border border-gray-200 overflow-hidden">
                                <div className="bg-primary h-3 rounded-full" style={{ width: summary.clinical_info.confidence.includes('%') ? summary.clinical_info.confidence : '85%' }}></div>
                            </div>
                            <p className="text-sm text-gray-600 font-medium text-right">Model Confidence Score: {summary.clinical_info.confidence}</p>
                        </div>
                    </div>

                    {/* PDF Medical Reasoning */}
                    {summary.clinical_info.medical_reasoning && summary.clinical_info.medical_reasoning.length > 0 && (
                        <div className="mb-8">
                            <h2 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4 flex items-center gap-2">
                                <Brain className="w-5 h-5 text-primary" /> Medical Reasoning Log
                            </h2>
                            <ul className="space-y-3 bg-gray-50 p-5 rounded-xl border border-gray-100">
                                {summary.clinical_info.medical_reasoning.map((reason, idx) => (
                                    <li key={idx} className="flex gap-3 text-sm text-gray-700">
                                        <span className="text-primary mt-0.5">•</span>
                                        <span className="leading-relaxed font-medium">{reason}</span>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {/* PDF Conversation History */}
                    {summary.conversation_logs && summary.conversation_logs.length > 0 && (
                        <div className="mb-8 break-inside-avoid">
                            <h2 className="text-lg font-bold text-gray-800 border-b border-gray-200 pb-2 mb-4 flex items-center gap-2">
                                <MessageSquare className="w-5 h-5 text-primary" /> Verbatim Chat History
                            </h2>
                            <div className="space-y-4">
                                {summary.conversation_logs.map((log, idx) => (
                                    <div key={idx} className={`flex flex-col ${log.role === 'user' ? 'items-end' : 'items-start'}`}>
                                        <p className="text-[10px] font-bold text-gray-400 mb-1 uppercase tracking-wider">{log.role === 'user' ? summary.patient.name : 'AI Doctor'}</p>
                                        <div className={`px-4 py-3 rounded-2xl max-w-[80%] text-sm leading-relaxed ${log.role === 'user' ? 'bg-primary/10 text-primary border border-primary/20 rounded-tr-sm' : 'bg-gray-100 text-gray-800 border border-gray-200 rounded-tl-sm'}`}>
                                            {log.content}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* PDF Footer elements */}
                    <div className="mt-12 pt-6 border-t border-gray-200 text-center">
                        <p className="text-xs font-bold text-gray-400 uppercase tracking-widest mb-2">Upchaar AI Automated System</p>
                        <p className="text-[10px] text-gray-500 italic max-w-2xl mx-auto leading-relaxed">
                            Disclaimer: This document is an automatically generated transcription and analysis produced by an AI system. Note: Diagnostic suggestions are purely for informational purposes and absolutely do not substitute professional medical evaluation or clinical testing.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}
