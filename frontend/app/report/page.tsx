"use client";

import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { useLanguage } from "@/context/LanguageContext";
import { useAuth } from "@/context/AuthContext";
import { doc, getDoc } from "firebase/firestore";
import { db } from "@/lib/firebase";
import { ThemeToggle } from "@/components/ui/ThemeToggle";
import { LanguageSwitcher } from "@/components/LanguageSwitcher";
import {
    FileText,
    Download,
    ArrowLeft,
    Printer,
    CheckCircle2,
    AlertCircle,
    LogOut
} from "lucide-react";
import jsPDF from "jspdf";
import Image from "next/image";

interface SessionData {
    username?: string;
    age?: number;
    gender?: string;
    language?: string;
    symptoms?: string;
    predictions?: {
        disease?: string;
    };
    risk_level?: string;
    guidance?: {
        first_aid?: string[];
        home_remedies?: string[];
        medicines?: Array<{ name: string; guidance: string }>;
        routine?: string[];
    };
    timestamp?: string;
}

export default function ReportPage() {
    const { lang } = useLanguage();
    const { user, userProfile } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get("id");

    const [data, setData] = useState<SessionData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (!user) {
            router.push("/");
            return;
        }

        if (sessionId) {
            const fetchSession = async () => {
                const docRef = doc(db, "sessions", sessionId);
                const docSnap = await getDoc(docRef);
                if (docSnap.exists()) {
                    setData(docSnap.data());
                }
                setLoading(false);
            };
            fetchSession();
        } else {
            setLoading(false);
        }
    }, [user, sessionId, router]);

    const reportTranslations = {
        en: {
            header: "UPCHAAR MEDICAL REPORT",
            patientInfo: "Patient Information",
            username: "Patient Name",
            age: "Age",
            gender: "Gender",
            lang: "Report Language",
            results: "Triage Assessment Results",
            symptoms: "Clinical Symptoms",
            condition: "Possible Condition",
            risk: "Risk Level",
            guidance: "Medical Guidance & Recommendations",
            firstAid: "First Aid Instructions",
            remedies: "Home Care & Remedies",
            medicines: "OTC Medicines (Consult Doctor Before Use)",
            routine: "Recovery Routine",
            warnings: "Critical Warnings",
            seekCare: "When to Seek Professional Care",
            generated: "Generated on"
        },
        hi: {
            header: "उपचार मेडिकल रिपोर्ट",
            patientInfo: "रोगी की जानकारी",
            username: "रोगी का नाम",
            age: "आयु",
            gender: "लिंग",
            lang: "रिपोर्ट की भाषा",
            results: "ट्राइएज मूल्यांकन परिणाम",
            symptoms: "नैदानिक लक्षण",
            condition: "संभावित स्थिति",
            risk: "जोखिम स्तर",
            guidance: "चिकित्सा मार्गदर्शन और सुझाव",
            firstAid: "प्राथमिक चिकित्सा निर्देश",
            remedies: "घरेलू उपचार और देखभाल",
            medicines: "OTC दवाएं (उपयोग से पहले डॉक्टर से सलाह लें)",
            routine: "स्वस्थ होने की दिनचर्या",
            warnings: "महत्वपूर्ण चेतावनियां",
            seekCare: "डॉक्टर से कब मिलें",
            generated: "पर तैयार किया गया"
        },
        mr: {
            header: "उपचार वैद्यकीय अहवाल",
            patientInfo: "रुग्णाची माहिती",
            username: "रुग्णाचे नाव",
            age: "वय",
            gender: "लिंग",
            lang: "अहवाल भाषा",
            results: "ट्रायेज मूल्यांकन निकाल",
            symptoms: "नैदानिक लक्षणे",
            condition: "संभाव्य स्थिती",
            risk: "धोका पातळी",
            guidance: "वैद्यकीय मार्गदर्शन आणि शिफारसी",
            firstAid: "प्रथम उपचार सूचना",
            remedies: "घरगुती उपाय आणि काळजी",
            medicines: "OTC औषधे (वापरण्यापूर्वी डॉक्टरांचा सल्ला घ्या)",
            routine: "पुनर्प्राप्ती दिनचर्या",
            warnings: "महत्वाच्या सूचना",
            seekCare: "डॉक्टरांना कधी भेटावे",
            generated: "रोजी तयार केले"
        }
    };

    const generatePDF = () => {
        if (!data) return;

        const doc = new jsPDF();
        const rT = reportTranslations[lang as keyof typeof reportTranslations] || reportTranslations.en;
        const margin = 20;
        let y = 20;

        // Header Decoration
        doc.setFillColor(245, 247, 250);
        doc.rect(0, 0, 210, 40, "F");

        // Header
        doc.setFontSize(22);
        doc.setTextColor(30, 41, 59);
        // Fallback for non-latin in standard jsPDF: we use English if font not loaded, 
        // but here we set up the structure.
        doc.text(rT.header, margin, y + 10);

        doc.setFontSize(9);
        doc.setTextColor(100);
        doc.text(`${rT.generated}: ${new Date().toLocaleString()}`, 140, y + 10);
        y += 35;

        // Patient Section
        doc.setFillColor(0, 153, 204);
        doc.rect(margin, y - 5, 170, 8, "F");
        doc.setTextColor(255);
        doc.setFontSize(11);
        doc.text(rT.patientInfo, margin + 5, y + 1);
        y += 12;

        doc.setTextColor(0);
        doc.setFontSize(10);
        const patientDetails = [
            [rT.username, userProfile?.fullName || data.username || user?.displayName || "N/A"],
            [rT.age, userProfile?.age || data.age || "N/A"],
            [rT.gender, userProfile?.gender || data.gender || "N/A"],
            [rT.lang, data.language?.toUpperCase() || "EN"]
        ];

        patientDetails.forEach(([label, value]) => {
            doc.setFont("helvetica", "bold");
            doc.text(`${label}:`, margin, y);
            doc.setFont("helvetica", "normal");
            doc.text(String(value), margin + 60, y);
            y += 7;
        });
        y += 10;

        // Triage Results Section
        doc.setFillColor(0, 153, 204);
        doc.rect(margin, y - 5, 170, 8, "F");
        doc.setTextColor(255);
        doc.text(rT.results, margin + 5, y + 1);
        y += 12;

        doc.setTextColor(0);
        const assessmentDetails = [
            [rT.symptoms, data.symptoms || "N/A"],
            [rT.condition, data.predictions?.disease || "N/A"],
            [rT.risk, data.risk_level || "Unknown"]
        ];

        assessmentDetails.forEach(([label, value]) => {
            doc.setFont("helvetica", "bold");
            doc.text(`${label}:`, margin, y);
            doc.setFont("helvetica", "normal");
            const splitVal = doc.splitTextToSize(String(value), 100);
            doc.text(splitVal, margin + 60, y);
            y += splitVal.length * 7;
        });
        y += 10;

        // Guidance Section
        doc.setFillColor(15, 23, 42);
        doc.rect(margin, y - 5, 170, 8, "F");
        doc.setTextColor(255);
        doc.text(rT.guidance, margin + 5, y + 1);
        y += 12;

        doc.setTextColor(0);
        const guidanceSections = [
            { label: rT.firstAid, data: data.guidance?.first_aid },
            { label: rT.remedies, data: data.guidance?.home_remedies },
            { label: rT.medicines, data: data.guidance?.medicines, type: 'meds' },
            { label: rT.routine, data: data.guidance?.routine }
        ];

        guidanceSections.forEach((section) => {
            if (section.data && section.data.length > 0) {
                if (y > 250) { doc.addPage(); y = 20; }
                doc.setFont("helvetica", "bold");
                doc.text(section.label, margin, y);
                y += 6;
                doc.setFont("helvetica", "normal");
                section.data.forEach((item: string | { name: string; guidance: string }) => {
                    const textContent = section.type === 'meds' ? `${(item as { name: string; guidance: string }).name}: ${(item as { name: string; guidance: string }).guidance}` : item;
                    const splitText = doc.splitTextToSize(`• ${textContent}`, 160);
                    doc.text(splitText, margin + 5, y);
                    y += splitText.length * 6;
                    if (y > 270) { doc.addPage(); y = 20; }
                });
                y += 5;
            }
        });

        doc.save(`Upchaar_Report_${data.timestamp}.pdf`);
    };

    if (loading) return <div className="min-h-screen flex items-center justify-center text-primary animate-pulse">Retrieving Medical Record...</div>;

    return (
        <main className="min-h-screen bg-hero-glow p-4 md:p-8">
            <div className="max-w-4xl mx-auto space-y-8">
                {/* Navbar */}
                <nav className="flex items-center justify-between bg-surface/40 backdrop-blur-xl border border-borderDark rounded-2xl px-6 py-3 shadow-glass">
                    <div className="flex items-center gap-3">
                        <button
                            onClick={() => router.push("/chat")}
                            className="p-3 hover:bg-primary/10 text-textMuted hover:text-primary rounded-xl transition-all flex items-center justify-center min-w-[44px] min-h-[44px]"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="w-px h-6 bg-borderDark hidden sm:block" />
                        <a
                            href="/logout"
                            className="p-3 hover:bg-danger/10 text-textMuted hover:text-danger rounded-xl transition-all flex items-center justify-center min-w-[44px] min-h-[44px]"
                            title="Sign Out"
                        >
                            <LogOut className="w-5 h-5" />
                        </a>
                        <ThemeToggle />
                        <LanguageSwitcher />
                    </div>
                </nav>

                {data ? (
                    <div className="glass-panel p-8 space-y-8">
                        <div className="flex flex-col md:flex-row justify-between items-start gap-6 border-b border-borderDark pb-8">
                            <div className="flex items-center gap-6">
                                <div className="w-16 h-16 relative rounded-full overflow-hidden bg-primary/5 border border-primary/10 shadow-sm">
                                    <Image src="/logo.png" alt="Logo" fill className="object-cover" />
                                </div>
                                <div>
                                    <div className="flex flex-col">
                                        <span className="font-heading font-bold text-2xl tracking-tight text-textMain leading-none">UPCHAAR</span>
                                        <span className="text-xs text-primary font-mono uppercase tracking-[0.2em] opacity-80 mt-2">ai rural triage</span>
                                    </div>
                                    <p className="text-textMuted font-mono text-[10px] uppercase mt-3 tracking-tighter">Medical Triage Record • Ref: {sessionId?.substring(0, 8)}</p>
                                </div>
                            </div>
                            <div className="flex gap-3">
                                <button
                                    onClick={generatePDF}
                                    className="px-6 py-3 bg-primary text-background rounded-xl font-bold flex items-center gap-2 hover:bg-primary/90 transition-all shadow-neon"
                                >
                                    <Download className="w-4 h-4" /> Download PDF
                                </button>
                                <button
                                    onClick={() => window.print()}
                                    className="px-6 py-3 bg-surface border border-borderDark hover:border-primary/50 text-textMain rounded-xl font-bold flex items-center gap-2 transition-all"
                                >
                                    <Printer className="w-4 h-4" /> Print
                                </button>
                            </div>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                            <section className="space-y-6">
                                <h2 className="text-sm font-bold text-primary uppercase tracking-widest flex items-center gap-2">
                                    <CheckCircle2 className="w-4 h-4" /> Patient Summary
                                </h2>
                                <div className="space-y-4">
                                    <div className="flex justify-between border-b border-white/5 pb-2">
                                        <span className="text-textMuted text-sm">Patient</span>
                                        <span className="text-textMain font-medium">{userProfile?.fullName || data.username || user?.displayName}</span>
                                    </div>
                                    <div className="flex justify-between border-b border-white/5 pb-2">
                                        <span className="text-textMuted text-sm">Age</span>
                                        <span className="text-textMain font-medium">{userProfile?.age || data.age}</span>
                                    </div>
                                    <div className="flex justify-between border-b border-white/5 pb-2">
                                        <span className="text-textMuted text-sm">Gender</span>
                                        <span className="text-textMain font-medium">{userProfile?.gender || data.gender}</span>
                                    </div>
                                    <div className="flex justify-between border-b border-white/5 pb-2">
                                        <span className="text-textMuted text-sm">Risk Assessment</span>
                                        <span className={`font-bold ${data.risk_level === 'Emergency' ? 'text-danger' : 'text-secondary'}`}>{data.risk_level}</span>
                                    </div>
                                </div>
                            </section>

                            <section className="space-y-6">
                                <h2 className="text-sm font-bold text-primary uppercase tracking-widest flex items-center gap-2">
                                    <AlertCircle className="w-4 h-4" /> Assessment Details
                                </h2>
                                <div className="space-y-4">
                                    <div className="flex flex-col gap-1">
                                        <span className="text-textMuted text-xs uppercase tracking-tighter">Clinical Symptoms</span>
                                        <span className="text-textMain text-sm leading-relaxed">{data.symptoms}</span>
                                    </div>
                                    <div className="flex flex-col gap-1">
                                        <span className="text-textMuted text-xs uppercase tracking-tighter">AI Diagnosis</span>
                                        <span className="text-secondary font-bold text-xl">{data.predictions?.disease}</span>
                                    </div>
                                </div>
                            </section>

                            {/* Medical Guidance Sections */}
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 border-t border-borderDark pt-8">
                                {data.guidance?.first_aid && data.guidance.first_aid.length > 0 && (
                                    <div className="space-y-3">
                                        <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-widest">🩹 First Aid</h3>
                                        <ul className="space-y-2">
                                            {data.guidance.first_aid.map((item: string, i: number) => (
                                                <li key={i} className="text-sm text-textMuted flex gap-2">
                                                    <span className="text-emerald-500/50">•</span>
                                                    {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {data.guidance?.home_remedies && data.guidance.home_remedies.length > 0 && (
                                    <div className="space-y-3">
                                        <h3 className="text-xs font-bold text-amber-500 uppercase tracking-widest">☕ Home Care</h3>
                                        <ul className="space-y-2">
                                            {data.guidance.home_remedies.map((item: string, i: number) => (
                                                <li key={i} className="text-sm text-textMuted flex gap-2">
                                                    <span className="text-amber-500/50">•</span>
                                                    {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}

                                {data.guidance?.medicines && data.guidance.medicines.length > 0 && (
                                    <div className="space-y-3">
                                        <h3 className="text-xs font-bold text-teal-400 uppercase tracking-widest">💊 OTC Medicines</h3>
                                        <div className="space-y-3">
                                            {data.guidance.medicines.map((med, i: number) => (
                                                <div key={i} className="bg-surfaceHighlight/30 p-3 rounded-xl border border-borderDark">
                                                    <p className="text-sm font-bold text-textMain">{med.name}</p>
                                                    <p className="text-xs text-textMuted mt-1">{med.guidance}</p>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {data.guidance?.routine && data.guidance.routine.length > 0 && (
                                    <div className="space-y-3">
                                        <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest">📅 Recovery Routine</h3>
                                        <ul className="space-y-2">
                                            {data.guidance.routine.map((item: string, i: number) => (
                                                <li key={i} className="text-sm text-textMuted flex gap-2">
                                                    <span className="text-blue-500/50">•</span>
                                                    {item}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                ) : (
                    <div className="glass-panel p-12 text-center text-textMuted">
                        <FileText className="w-12 h-12 mx-auto mb-4 opacity-20" />
                        No report session found. Please go to Chat to generate a report.
                    </div>
                )}
            </div>
        </main>
    );
}
