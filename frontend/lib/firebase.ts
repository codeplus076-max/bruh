import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";

const firebaseConfig = {
    apiKey: process.env.NEXT_PUBLIC_FIREBASE_API_KEY || "AIzaSyDzsbrNLx-IUSWWjuRmg0PeO0KXncQwsPo",
    authDomain: process.env.NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN || "nono-9254c.firebaseapp.com",
    projectId: process.env.NEXT_PUBLIC_FIREBASE_PROJECT_ID || "nono-9254c",
    storageBucket: process.env.NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET || "nono-9254c.firebasestorage.app",
    messagingSenderId: process.env.NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID || "789441117162",
    appId: process.env.NEXT_PUBLIC_FIREBASE_APP_ID || "1:789441117162:web:e74489b54d34ffca371093",
};

// Initialize Firebase with real keys
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

const auth = getAuth(app);
const db = getFirestore(app);

export { auth, db };
