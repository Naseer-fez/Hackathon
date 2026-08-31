import React, { useState } from "react";
import { Navbar } from "./components/Navbar";
import { RecommendationTab } from "./components/RecommendationTab";
import { TenderAnalyzerView } from "./components/TenderAnalyzerView";
import { KnowledgeGraphView } from "./components/KnowledgeGraphView";
import { QcoExplorerView } from "./components/QcoExplorerView";
import { GemSimulatorView } from "./components/GemSimulatorView";
import { AssistantChatDrawer } from "./components/AssistantChatDrawer";

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState("recommend");
  const [pdfText, setPdfText] = useState<string>("");

  return (
    <div className="min-h-screen bg-apple-bg text-slate-100 flex flex-col font-sans selection:bg-apple-blue selection:text-white">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main 
        className={`flex-1 w-full mx-auto relative ${
          activeTab === "graph" ? "max-w-none p-0" : "max-w-7xl p-6 space-y-6 pt-24"
        }`}
      >
        {activeTab === "recommend" && <RecommendationTab />}
        {activeTab === "tender" && <TenderAnalyzerView setPdfText={setPdfText} />}
        {activeTab === "graph" && <KnowledgeGraphView />}
        {activeTab === "qco" && <QcoExplorerView />}
        {activeTab === "gem" && <GemSimulatorView />}
      </main>

      <AssistantChatDrawer pdfText={pdfText} />
    </div>
  );
};

export default App;

