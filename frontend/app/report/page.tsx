"use client";

import { useState, useEffect, Suspense } from "react";
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
    AlertCircle
} from "lucide-react";
import jsPDF from "jspdf";
import Image from "next/image";

export default function ReportPage() {
    const { t, lang } = useLanguage();
    const { user } = useAuth();
    const router = useRouter();
    const searchParams = useSearchParams();
    const sessionId = searchParams.get("id");

    const [data, setData] = useState<any>(null);
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

    const generatePDF = () => {
        if (!data) return;

        const doc = new jsPDF();
        const margin = 20;
        let y = 20;

        // Header
        doc.setFontSize(22);
        doc.setTextColor(0, 153, 204);
        doc.text("UPCHAAR MEDICAL REPORT", margin, y);
        y += 10;

        doc.setFontSize(10);
        doc.setTextColor(100);
        doc.text(`Generated on: ${new Date().toLocaleString()}`, margin, y);
        y += 15;

        // User Info
        doc.setFontSize(14);
        doc.setTextColor(0);
        doc.text("Patient Information", margin, y);
        y += 10;
        doc.setFontSize(11);
        doc.text(`Username: ${data.username || "N/A"}`, margin, y);
        y += 7;
        doc.text(`Age: ${data.age}`, margin, y);
        y += 7;
        doc.text(`Language: ${data.language}`, margin, y);
        y += 15;

        // Clinical Data
        doc.setFontSize(14);
        doc.text("Triage Results", margin, y);
        y += 10;
        doc.setFontSize(11);
        doc.text(`Symptoms: ${data.symptoms}`, margin, y);
        y += 7;
        doc.text(`Predicted Condition: ${data.predictions?.disease}`, margin, y);
        y += 7;
        doc.text(`Risk Level: ${data.risk_level}`, margin, y);
        y += 15;

        // Guidance
        doc.setFontSize(14);
        doc.text("Medical Guidance", margin, y);
        y += 10;
        doc.setFontSize(10);

        if (data.guidance?.first_aid?.length > 0) {
            doc.text("First Aid:", margin, y);
            y += 5;
            data.guidance.first_aid.forEach((item: string) => {
                const splitText = doc.splitTextToSize(`• ${item}`, 170);
                doc.text(splitText, margin + 5, y);
                y += splitText.length * 5;
            });
        }

        // Add more sections as needed...

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
                            className="p-2 hover:bg-primary/10 text-textMuted hover:text-primary rounded-xl transition-all"
                        >
                            <ArrowLeft className="w-5 h-5" />
                        </button>
                    </div>
                    <div className="flex items-center gap-4">
                        <ThemeToggle />
                        <LanguageSwitcher />
                    </div>
                </nav>

                {data ? (
                    <div className="glass-panel p-8 space-y-8">
                        <div className="flex flex-col md:flex-row justify-between items-start gap-6 border-b border-borderDark pb-8">
                            <div className="flex items-center gap-6">
                                <div className="w-20 h-20 relative bg-primary/10 rounded-2xl border border-primary/20 p-4">
                                    <Image src="/logo.png" alt="Logo" fill className="object-contain p-2" />
                                </div>
                                <div>
                                    <h1 className="text-3xl font-heading font-bold text-textMain tracking-tight">Medical Triage Report</h1>
                                    <p className="text-textMuted font-mono text-xs uppercase mt-1">Ref: {sessionId?.substring(0, 8)}</p>
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
                                        <span className="text-textMain font-medium">{data.username || user?.displayName}</span>
                                    </div>
                                    <div className="flex justify-between border-b border-white/5 pb-2">
                                        <span className="text-textMuted text-sm">Age</span>
                                        <span className="text-textMain font-medium">{data.age}</span>
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
                                        <span className="text-secondary font-bold text-lg">{data.predictions?.disease}</span>
                                    </div>
                                </div>
                            </section>
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
