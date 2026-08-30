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

  return (
    <div className="min-h-screen bg-[#070c18] text-slate-100 flex flex-col font-sans selection:bg-blue-600">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />

      <main className="flex-1 max-w-7xl w-full mx-auto p-6 space-y-6">
        {activeTab === "recommend" && <RecommendationTab />}
        {activeTab === "tender" && <TenderAnalyzerView />}
        {activeTab === "graph" && <KnowledgeGraphView />}
        {activeTab === "qco" && <QcoExplorerView />}
        {activeTab === "gem" && <GemSimulatorView />}
      </main>

      <AssistantChatDrawer />
    </div>
  );
};

export default App;

