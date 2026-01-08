// 临时测试文件：检查 API 连接
import { useEffect } from 'react';

export const TestConnection = () => {
    useEffect(() => {
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
        console.log('🔍 API URL:', apiUrl);
        
        // 测试 API 连接
        fetch(`${apiUrl}/airlines/top-rated`)
            .then(res => res.json())
            .then(data => {
                console.log('✅ API 连接成功:', data);
            })
            .catch(err => {
                console.error('❌ API 连接失败:', err);
            });
    }, []);
    
    return <div>检查控制台...</div>;
};

