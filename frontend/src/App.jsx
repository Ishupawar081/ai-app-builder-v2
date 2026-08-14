import { useState, useEffect } from 'react';
import { Panel, Group as PanelGroup, Separator as PanelResizeHandle } from 'react-resizable-panels';
import Editor from '@monaco-editor/react';
import { File, Folder, Search, GitBranch, Settings, Play, Check, Copy, User, ChevronRight, ChevronDown, TerminalSquare, MessageSquare } from 'lucide-react';
import { fetchFiles, fetchFileContent, saveFile, runCommand, generatePlan, buildApp, startDevServer, updateApp } from './api';

export default function App() {
  const [files, setFiles] = useState([]);
  const [activeFile, setActiveFile] = useState(null);
  const [fileContent, setFileContent] = useState('');
  const [terminalOutput, setTerminalOutput] = useState('Welcome to the integrated terminal.\n');
  const [terminalInput, setTerminalInput] = useState('');
  const [chatInput, setChatInput] = useState('');
  const [plan, setPlan] = useState(null);
  const [isGeneratingPlan, setIsGeneratingPlan] = useState(false);
  const [isBuilding, setIsBuilding] = useState(false);
  const [activeTab, setActiveTab] = useState('code'); // 'code' or 'preview'
  const [isPreviewRunning, setIsPreviewRunning] = useState(false);
  const [isAppBuilt, setIsAppBuilt] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);

  useEffect(() => {
    loadFiles();
  }, []);

  const loadFiles = async () => {
    try {
      const data = await fetchFiles();
      setFiles(data.files);
    } catch (e) {
      console.error(e);
    }
  };

  const handleFileClick = async (path) => {
    setActiveFile(path);
    setActiveTab('code');
    try {
      const data = await fetchFileContent(path);
      setFileContent(data.content);
    } catch (e) {
      setFileContent('Error loading file content.');
    }
  };

  const handleEditorChange = (value) => {
    setFileContent(value);
  };

  const handleSave = async () => {
    if (activeFile) {
      await saveFile(activeFile, fileContent);
    }
  };

  const handleTerminalCommand = async (e) => {
    if (e.key === 'Enter' && terminalInput.trim()) {
      const cmd = terminalInput;
      setTerminalOutput((prev) => prev + `\n$ ${cmd}\nRunning...`);
      setTerminalInput('');
      try {
        const data = await runCommand(cmd);
        setTerminalOutput((prev) => prev.replace('Running...', data.output));
      } catch (err) {
        setTerminalOutput((prev) => prev.replace('Running...', 'Command failed.'));
      }
    }
  };

  const handleGeneratePlan = async () => {
    if (!chatInput.trim()) return;
    setIsGeneratingPlan(true);
    setTerminalOutput((prev) => prev + `\n> Generating plan for: ${chatInput}\n`);
    try {
      const planData = await generatePlan(chatInput);
      setPlan(planData.plan);
      setTerminalOutput((prev) => prev + `> Plan generated. Ready to build.\n`);
    } catch (e) {
      setTerminalOutput((prev) => prev + `> Error generating plan: ${e.message}\n`);
    } finally {
      setIsGeneratingPlan(false);
    }
  };

  const handleBuildApp = async () => {
    if (!plan) return;
    setIsBuilding(true);
    setTerminalOutput((prev) => prev + `> Starting build for ${plan.app_name}...\n`);
    try {
      const buildData = await buildApp(chatInput, plan);
      setTerminalOutput((prev) => prev + `> Build output:\n${buildData.result}\n`);
      setIsAppBuilt(true);
      loadFiles(); // Refresh file explorer
    } catch (e) {
      setTerminalOutput((prev) => prev + `> Error building app: ${e.message}\n`);
    } finally {
      setIsBuilding(false);
      setChatInput('');
    }
  };

  const handleUpdateApp = async () => {
    if (!chatInput.trim()) return;
    setIsUpdating(true);
    setTerminalOutput((prev) => prev + `\n> Updating App...\n`);
    try {
      const res = await updateApp(chatInput);
      setTerminalOutput((prev) => prev + `> Update output:\n${res.result || 'App updated successfully'}\n`);
      loadFiles();
      setChatInput('');
    } catch (err) {
      setTerminalOutput((prev) => prev + `> Update Error: ${err.message}\n`);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleStartPreview = async () => {
    setTerminalOutput((prev) => prev + `\n> Starting Dev Server...\n`);
    try {
      const data = await startDevServer();
      setTerminalOutput((prev) => prev + `> ${data.message}\n`);
      setIsPreviewRunning(true);
      setActiveTab('preview');
    } catch (e) {
      setTerminalOutput((prev) => prev + `> Error starting preview: ${e.message}\n`);
    }
  };

  const renderPlan = (p) => {
    if (!p) return null;
    return (
      <div className="text-gray-300 text-sm space-y-4">
        <div>
          <h3 className="text-white font-bold text-base mb-1">{p.app_name}</h3>
          <p className="text-gray-400">{p.description}</p>
        </div>
        
        {p.features && p.features.length > 0 && (
          <div>
            <h4 className="text-vs-blue font-semibold mb-1">Key Features</h4>
            <ul className="list-disc pl-5 space-y-1">
              {p.features.map((f, i) => <li key={i}>{f}</li>)}
            </ul>
          </div>
        )}

        {p.tech_stack && p.tech_stack.length > 0 && (
          <div>
            <h4 className="text-vs-blue font-semibold mb-1">Tech Stack</h4>
            <div className="flex flex-wrap gap-2">
              {p.tech_stack.map((t, i) => (
                <span key={i} className="bg-[#2d2d2d] px-2 py-0.5 rounded text-xs">{t}</span>
              ))}
            </div>
          </div>
        )}

        {p.planning_step && p.planning_step.summary && (
          <div>
            <h4 className="text-vs-blue font-semibold mb-1">Architecture</h4>
            <p className="text-gray-400 text-xs leading-relaxed">{p.planning_step.summary}</p>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="flex h-screen w-screen bg-vs-bg text-vs-text font-inter overflow-hidden">
      
      {/* Activity Bar */}
      <div className="w-12 bg-vs-activity flex flex-col items-center py-4 border-r border-vs-border gap-6">
        <div className="p-2 cursor-pointer text-gray-400 hover:text-white"><File size={24} strokeWidth={1.5} /></div>
        <div className="p-2 cursor-pointer text-gray-400 hover:text-white"><Search size={24} strokeWidth={1.5} /></div>
        <div className="p-2 cursor-pointer text-gray-400 hover:text-white"><GitBranch size={24} strokeWidth={1.5} /></div>
        <div className="p-2 cursor-pointer text-gray-400 hover:text-white mt-auto"><User size={24} strokeWidth={1.5} /></div>
        <div className="p-2 cursor-pointer text-gray-400 hover:text-white"><Settings size={24} strokeWidth={1.5} /></div>
      </div>

      <PanelGroup direction="horizontal" orientation="horizontal" className="flex-1 w-full h-full">
        
        {/* Sidebar */}
        <Panel defaultSize="15%" minSize="10%" maxSize="30%">
          <div className="h-full bg-vs-sidebar border-r border-vs-border flex flex-col">
            <div className="uppercase text-xs font-semibold px-4 py-3 tracking-wider text-gray-400">
              Explorer
            </div>
            <div className="flex-1 overflow-y-auto">
              <div className="px-4 pb-3 mb-2 border-b border-vs-border">
                 <div className="text-[10px] text-gray-500 mb-1">Code Directory:</div>
                 <div className="text-[11px] text-gray-300 font-mono break-all mb-3 bg-[#1e1e1e] p-1.5 rounded">../projects/app_main_app</div>
                 <a href="http://localhost:8000/api/download" download className="block w-full text-center bg-[#333333] hover:bg-[#444444] text-gray-200 text-xs py-1.5 rounded transition-colors flex items-center justify-center gap-1.5">
                   <Folder size={12} /> Download Folder (.zip)
                 </a>
              </div>
              <div className="px-2 py-1 text-sm font-semibold flex items-center gap-1 cursor-pointer hover:bg-vs-hover">
                <ChevronDown size={16} /> APP_MAIN_APP
              </div>
              <div className="pl-6 py-1 text-sm flex items-center gap-2 cursor-pointer hover:bg-vs-hover">
                <Folder size={14} className="text-blue-400" /> src
              </div>
              {files.map((file, i) => (
                <div 
                  key={i} 
                  className={`pl-10 py-1 text-sm flex items-center gap-2 cursor-pointer ${activeFile === file ? 'bg-vs-active text-white' : 'hover:bg-vs-hover'}`}
                  onClick={() => handleFileClick(file)}
                >
                  <File size={14} className="text-gray-400" /> 
                  {file.split('/').pop()}
                </div>
              ))}
            </div>
          </div>
        </Panel>
        
        <PanelResizeHandle className="w-1 bg-vs-border hover:bg-vs-blue transition-colors cursor-col-resize" />
        
        {/* Main Editor & Terminal Area */}
        <Panel defaultSize="60%">
          <PanelGroup direction="vertical" orientation="vertical" className="w-full h-full">
            {/* Editor Area */}
            <Panel defaultSize="70%">
              <div className="h-full flex flex-col bg-vs-bg">
                {/* Editor Tabs */}
                <div className="flex bg-[#2d2d2d] overflow-x-auto hide-scrollbar">
                  {activeFile ? (
                    <div 
                      onClick={() => setActiveTab('code')}
                      className={`px-4 py-2 text-sm flex items-center gap-2 cursor-pointer ${activeTab === 'code' ? 'bg-vs-bg text-white border-t border-vs-blue' : 'text-gray-400 hover:bg-[#333333]'}`}
                    >
                      <span className="text-yellow-400">JS</span> {activeFile.split('/').pop()}
                    </div>
                  ) : (
                    <div className="px-4 py-2 text-sm text-gray-400">Welcome</div>
                  )}
                  <div 
                    onClick={() => setActiveTab('preview')}
                    className={`px-4 py-2 text-sm flex items-center gap-2 cursor-pointer ${activeTab === 'preview' ? 'bg-vs-bg text-white border-t border-vs-blue' : 'text-gray-400 hover:bg-[#333333]'}`}
                  >
                    <Play size={14} /> Preview
                  </div>
                </div>
                
                {/* Breadcrumbs */}
                {activeFile && (
                  <div className="px-4 py-1 text-xs text-gray-400 border-b border-vs-border flex items-center gap-2">
                    <span>app_main_app</span> <ChevronRight size={12}/> 
                    <span>src</span> <ChevronRight size={12}/> 
                    <span className="text-gray-300">{activeFile.split('/').pop()}</span>
                    
                    <button onClick={handleSave} className="ml-auto px-2 py-0.5 rounded hover:bg-vs-hover text-gray-300">
                      Save (Ctrl+S)
                    </button>
                  </div>
                )}
                
                {/* Code Editor or Preview */}
                <div className="flex-1 overflow-hidden">
                  {activeTab === 'preview' ? (
                    <div className="w-full h-full bg-white flex flex-col">
                      <div className="bg-[#f3f3f3] border-b border-[#cccccc] px-4 py-2 flex items-center gap-2">
                        <span className="text-sm font-semibold text-gray-700">App Preview</span>
                        <span className="text-xs text-gray-500 ml-auto">localhost:5174</span>
                        {!isPreviewRunning && (
                          <button onClick={handleStartPreview} className="bg-[#0e639c] hover:bg-[#1177bb] text-white px-3 py-1 rounded text-xs ml-2">
                            Start Server
                          </button>
                        )}
                      </div>
                      {isPreviewRunning ? (
                        <iframe src="http://localhost:5174" className="w-full h-full border-none" title="preview" />
                      ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-500 gap-4 bg-gray-50">
                          <Play size={48} className="text-gray-300"/>
                          <p>Dev server is not running.</p>
                          <button onClick={handleStartPreview} className="bg-[#0e639c] hover:bg-[#1177bb] text-white px-4 py-2 rounded shadow transition-colors">Start Dev Server</button>
                        </div>
                      )}
                    </div>
                  ) : activeFile ? (
                    <Editor
                      height="100%"
                      theme="vs-dark"
                      path={activeFile}
                      defaultLanguage="javascript"
                      value={fileContent}
                      onChange={handleEditorChange}
                      options={{ minimap: { enabled: false }, fontSize: 13, wordWrap: 'on' }}
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      Select a file to edit
                    </div>
                  )}
                </div>
              </div>
            </Panel>
            
            <PanelResizeHandle className="h-1 bg-vs-border hover:bg-vs-blue transition-colors cursor-row-resize" />
            
            {/* Terminal Area */}
            <Panel defaultSize="30%">
              <div className="h-full bg-vs-bg flex flex-col">
                <div className="flex border-b border-vs-border">
                  <div className="px-4 py-2 text-xs uppercase tracking-wide text-gray-400 hover:text-white cursor-pointer">Problems</div>
                  <div className="px-4 py-2 text-xs uppercase tracking-wide text-gray-400 hover:text-white cursor-pointer border-b border-vs-blue text-white">Terminal</div>
                  <div className="px-4 py-2 text-xs uppercase tracking-wide text-gray-400 hover:text-white cursor-pointer">Output</div>
                  <div className="px-4 py-2 text-xs uppercase tracking-wide text-gray-400 hover:text-white cursor-pointer">Ports</div>
                </div>
                <div className="flex-1 p-2 font-mono text-sm overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-gray-300">{terminalOutput}</pre>
                  <div className="flex items-center mt-1">
                    <span className="text-green-400 mr-2">vaishnavi@ai-builder:~$</span>
                    <input 
                      type="text" 
                      className="flex-1 bg-transparent outline-none border-none text-white"
                      value={terminalInput}
                      onChange={(e) => setTerminalInput(e.target.value)}
                      onKeyDown={handleTerminalCommand}
                      spellCheck="false"
                    />
                  </div>
                </div>
              </div>
            </Panel>
          </PanelGroup>
        </Panel>

        <PanelResizeHandle className="w-1 bg-vs-border hover:bg-vs-blue transition-colors cursor-col-resize" />
        
        {/* AI App Builder Panel */}
        <Panel defaultSize="25%" minSize="15%">
          <div className="h-full bg-vs-sidebar flex flex-col">
            <div className="px-4 py-3 font-semibold text-sm border-b border-vs-border flex items-center gap-2">
              <MessageSquare size={16} className="text-blue-400"/> AI App Builder
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-4">
              <div className="text-sm text-gray-300">
                Hi! I'm your AI App Builder agent. I can generate a full-stack Vite + Express application for you.
              </div>
              
              <div className="bg-[#1e1e1e] p-3 rounded-lg border border-vs-border text-sm">
                <div className="font-semibold mb-2">{isAppBuilt ? 'Modify App' : 'Build an App'}</div>
                <textarea 
                  className="w-full bg-[#2d2d2d] text-white p-2 rounded outline-none border border-transparent focus:border-vs-blue resize-none h-24 mb-3 font-inter"
                  placeholder={isAppBuilt ? "e.g. Add a dark mode toggle..." : "e.g. A task manager with kanban board..."}
                  value={chatInput}
                  onChange={(e) => setChatInput(e.target.value)}
                  disabled={isGeneratingPlan || isBuilding || isUpdating}
                />
                {!plan ? (
                  <button 
                    className="w-full bg-[#0e639c] hover:bg-[#1177bb] text-white py-1.5 rounded transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                    onClick={handleGeneratePlan}
                    disabled={isGeneratingPlan || !chatInput.trim()}
                  >
                    {isGeneratingPlan ? 'Generating Plan...' : <><Play size={14} /> Generate Plan</>}
                  </button>
                ) : (
                  <div className="flex flex-col gap-2">
                    <div className="flex gap-2">
                      <button 
                        className="flex-1 bg-[#333333] hover:bg-[#444444] text-white py-1.5 rounded transition-colors"
                        onClick={() => { setPlan(null); setIsAppBuilt(false); }}
                        disabled={isBuilding || isUpdating}
                      >
                        Reset
                      </button>
                      {!isAppBuilt ? (
                        <button 
                          className="flex-2 bg-[#0e639c] hover:bg-[#1177bb] text-white py-1.5 px-4 rounded transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                          onClick={handleBuildApp}
                          disabled={isBuilding}
                        >
                          {isBuilding ? 'Building...' : <><Check size={14} /> Build App</>}
                        </button>
                      ) : (
                        <button 
                          className="flex-2 bg-[#0e639c] hover:bg-[#1177bb] text-white py-1.5 px-4 rounded transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                          onClick={handleUpdateApp}
                          disabled={isUpdating || !chatInput.trim()}
                        >
                          {isUpdating ? 'Updating...' : <><Check size={14} /> Update App</>}
                        </button>
                      )}
                    </div>
                    <button 
                      className="w-full bg-[#047857] hover:bg-[#059669] text-white py-1.5 rounded transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                      onClick={handleStartPreview}
                    >
                      <Play size={14} /> Run Dev Server
                    </button>
                  </div>
                )}
              </div>

              {plan && (
                <div className="bg-[#1e1e1e] p-4 rounded-lg border border-vs-border overflow-y-auto max-h-[60vh]">
                  {renderPlan(plan)}
                </div>
              )}
            </div>
          </div>
        </Panel>

      </PanelGroup>
    </div>
  );
}
