import React from 'react';

const Footer = () => {
    return (
        <div className="bg-white">
            <div className="footer my-[100px] mx-[200px] mb-[20px]">
                <div className="top flex gap-[50px]">
                    <div className="item flex-1 flex flex-col gap-[10px] text-justify text-[14px]">
                        <h1 className="text-[18px] font-medium text-gray-500">Links</h1>
                        <span className="text-gray-500">FAQ</span>
                        <span className="text-gray-500">Pages</span>
                        <span className="text-gray-500">Stores</span>
                        <span className="text-gray-500">Compare</span>
                        <span className="text-gray-500">Cookies</span>
                    </div>
                    <div className="item flex-1 flex flex-col gap-[10px] text-justify text-[14px]">
                        <h1 className="text-[18px] font-medium text-gray-500">About</h1>
                        <span className="text-gray-500">
                            A data project for marketing analysis. Sixty thousand reviews from 21 airlines are mined and analyzed by sentimental analysis, topic mining, OLS factor analysis, and RAG.
                        </span>
                    </div>
                    <div className="item flex-1 flex flex-col gap-[10px] text-justify text-[14px]">
                        <h1 className="text-[18px] font-medium text-gray-500">Contact</h1>
                        <span className="text-gray-500">
                            Ke CHEN <br />
                            Faidon KOTSAKIS <br />
                            Yuhong LI <br />
                            Bingjing YUE <br />
                            Wanchao ZHAO    
                        </span>
                    </div>
                </div>
                <div className="bottom flex items-center justify-between mt-[20px]">
                    <div className="left flex items-center">
                        <span className="copyright text-[12px] text-gray-500">
                            © Marketing analysis project (DSBA 2025). All Rights Reserved.
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Footer;