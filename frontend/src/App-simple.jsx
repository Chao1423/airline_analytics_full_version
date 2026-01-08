// 简化版 App 用于测试
import "./App.css";
import { Routes, Route } from "react-router-dom";
import { Toaster } from 'react-hot-toast';

import Dashboard from "./pages/dashboard/Dashboard";
import ReviewData from "./pages/reviewdata/ReviewData";
import Analytics from "./pages/analytics/Analytics";

import { TopBar } from "./components/NavBar/TopBar";
import SideMenu from "./components/NavBar/SideMenu";
import Footer from "./components/Footer/Footer";

function App() {
    console.log('🚀 App 组件已加载');
    console.log('📍 API URL:', import.meta.env.VITE_API_URL);
    
    return (
        <div>
            <div className="min-h-screen flex bg-gray-50">
                <SideMenu />
                <div className="flex flex-1 flex-col overflow-hidden">
                    <TopBar />
                    <div className="flex flex-1">
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/review-data" element={<ReviewData />} />
                            <Route path="/analytics" element={<Analytics />} />
                        </Routes>
                    </div>
                </div>
            </div>
            <Footer />
            <Toaster />
        </div>
    );
}

export default App;

