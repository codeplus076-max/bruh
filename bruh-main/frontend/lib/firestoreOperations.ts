import { doc, setDoc, collection, addDoc, getDocs, query, orderBy, where } from "firebase/firestore";
import { db } from "./firebase";
import { ParsedSnapshot } from "./dashboardUtils";

// 1. Create or Update Top-Level Episode Meta
export async function saveEpisodeMeta(userId: string, episodeId: string | null, snapshot: ParsedSnapshot): Promise<string> {
    const id = episodeId || `EP-${Date.now()}`;
    const episodeRef = doc(db, "episodes", id);
    
    await setDoc(episodeRef, {
        user_id: userId,
        title: snapshot.episode_context.title,
        status: snapshot.status,
        trend: snapshot.progression.trend,
        risk_level: snapshot.risk.level,
        severity_latest: snapshot.progression.day,
        updated_at: new Date().toISOString(),
        is_active: snapshot.episode_context.status !== "Recovered"
    }, { merge: true });

    return id;
}

// 2. Append Message securely bounds to Episode mapping
export async function saveMessageTick(episodeId: string, role: "user" | "assistant", markdown: string, snapshot?: ParsedSnapshot | null) {
    const messagesRef = collection(db, `episodes/${episodeId}/messages`);
    await addDoc(messagesRef, {
        role,
        content: markdown,
        parsed_snapshot: snapshot || null,
        timestamp: new Date().toISOString()
    });
}

// 3. Fetch User Episodes for the Sidebar
export async function fetchUserEpisodes(userId: string) {
    const q = query(collection(db, "episodes"), where("user_id", "==", userId), orderBy("updated_at", "desc"));
    const snapshot = await getDocs(q);
    return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}

// 4. Fetch Messages for specific Episode Reopen
export async function fetchEpisodeMessages(episodeId: string) {
    const q = query(collection(db, `episodes/${episodeId}/messages`), orderBy("timestamp", "asc"));
    const snapshot = await getDocs(q);
    return snapshot.docs.map(d => ({ id: d.id, ...d.data() }));
}
