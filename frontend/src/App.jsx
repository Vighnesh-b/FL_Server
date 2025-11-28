import React, { useState, useEffect } from 'react';
import { Activity, Users, Layers, Clock, RefreshCw, CheckCircle, AlertCircle, Server } from 'lucide-react';

const ServerDashboard = () => {
  const [serverStats, setServerStats] = useState({
    connectedClients: 0,
    totalRounds: 0,
    currentRound: 0,
    globalModelVersion: '1.0.0',
    lastAggregation: null,
    serverStatus: 'online'
  });

  const [clientLogs, setClientLogs] = useState([]);
  const [isAggregating, setIsAggregating] = useState(false);
  const [serverConfig, setServerConfig] = useState({
    serverIP: 'localhost:5000',
    minClientsRequired: 1,
    aggregationMethod: 'FedAvg'
  });

  useEffect(() => {
    fetchServerStatus();
    const interval = setInterval(fetchServerStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchServerStatus = async () => {
    try {
      const response = await fetch(`http://${serverConfig.serverIP}/server-status`);
      const data = await response.json();
      setServerStats(prev => ({ ...prev, ...data }));
    } catch (error) {
      console.error('Failed to fetch server status:', error);
      setServerStats(prev => ({ ...prev, serverStatus: 'offline' }));
    }
  };

  const fetchClientLogs = async () => {
    try {
      const response = await fetch(`http://${serverConfig.serverIP}/client-logs`);
      const data = await response.json();
      setClientLogs(data.logs || []);
    } catch (error) {
      console.error('Failed to fetch client logs:', error);
    }
  };

  const runFedAvg = async () => {
    setIsAggregating(true);
    try {
      const response = await fetch(`http://${serverConfig.serverIP}/aggregate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      const data = await response.json();
      
      setServerStats(prev => ({
        ...prev,
        currentRound: prev.currentRound + 1,
        totalRounds: prev.totalRounds + 1,
        lastAggregation: new Date().toISOString(),
        globalModelVersion: data.version || prev.globalModelVersion
      }));

      addLogEntry('System', 'Manual FedAvg aggregation completed', 'success');
    } catch (error) {
      console.error('Aggregation failed:', error);
      addLogEntry('System', 'FedAvg aggregation failed', 'error');
    } finally {
      setIsAggregating(false);
    }
  };

  const addLogEntry = (clientId, message, status) => {
    const newLog = {
      id: Date.now(),
      clientId,
      message,
      status,
      timestamp: new Date().toISOString()
    };
    setClientLogs(prev => [newLog, ...prev].slice(0, 50));
  };

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Never';
    return new Date(timestamp).toLocaleString();
  };

  const timeAgo = (timestamp) => {
    if (!timestamp) return 'Never';
    const seconds = Math.floor((new Date() - new Date(timestamp)) / 1000);
    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">Federated Learning Server</h1>
              <p className="text-purple-300">Admin Dashboard & Monitoring</p>
            </div>
            <div className="flex items-center gap-3">
              <div className={`px-4 py-2 rounded-full flex items-center gap-2 ${
                serverStats.serverStatus === 'online' ? 'bg-green-500/20 text-green-300' : 'bg-red-500/20 text-red-300'
              }`}>
                <div className={`w-2 h-2 rounded-full ${
                  serverStats.serverStatus === 'online' ? 'bg-green-400' : 'bg-red-400'
                } animate-pulse`}></div>
                {serverStats.serverStatus.toUpperCase()}
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-blue-500/20 rounded-lg">
                <Users className="w-6 h-6 text-blue-400" />
              </div>
              <span className="text-blue-300 text-sm font-medium">Active</span>
            </div>
            <h3 className="text-3xl font-bold text-white mb-1">{serverStats.connectedClients}</h3>
            <p className="text-slate-300 text-sm">Connected Clients</p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-purple-500/20 rounded-lg">
                <RefreshCw className="w-6 h-6 text-purple-400" />
              </div>
              <span className="text-purple-300 text-sm font-medium">Round</span>
            </div>
            <h3 className="text-3xl font-bold text-white mb-1">{serverStats.currentRound}</h3>
            <p className="text-slate-300 text-sm">Current Training Round</p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-green-500/20 rounded-lg">
                <Layers className="w-6 h-6 text-green-400" />
              </div>
              <span className="text-green-300 text-sm font-medium">Version</span>
            </div>
            <h3 className="text-3xl font-bold text-white mb-1">{serverStats.globalModelVersion}</h3>
            <p className="text-slate-300 text-sm">Global Model</p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20 hover:bg-white/15 transition-all">
            <div className="flex items-center justify-between mb-4">
              <div className="p-3 bg-amber-500/20 rounded-lg">
                <Clock className="w-6 h-6 text-amber-400" />
              </div>
              <span className="text-amber-300 text-sm font-medium">Updated</span>
            </div>
            <h3 className="text-2xl font-bold text-white mb-1">{timeAgo(serverStats.lastAggregation)}</h3>
            <p className="text-slate-300 text-sm">Last Aggregation</p>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Server className="w-5 h-5" />
                Control Panel
              </h2>

              <button
                onClick={runFedAvg}
                disabled={isAggregating || serverStats.connectedClients < serverConfig.minClientsRequired}
                className={`w-full py-3 px-4 rounded-lg font-semibold transition-all flex items-center justify-center gap-2 mb-4 ${
                  isAggregating || serverStats.connectedClients < serverConfig.minClientsRequired
                    ? 'bg-gray-500/50 text-gray-300 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white shadow-lg hover:shadow-xl'
                }`}
              >
                {isAggregating ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin" />
                    Aggregating...
                  </>
                ) : (
                  <>
                    <Activity className="w-5 h-5" />
                    Run FedAvg Now
                  </>
                )}
              </button>

              {serverStats.connectedClients < serverConfig.minClientsRequired && (
                <div className="bg-amber-500/20 border border-amber-500/30 rounded-lg p-3 mb-4">
                  <p className="text-amber-200 text-sm flex items-center gap-2">
                    <AlertCircle className="w-4 h-4" />
                    Need {serverConfig.minClientsRequired - serverStats.connectedClients} more client(s)
                  </p>
                </div>
              )}

              <button onClick={fetchClientLogs} className="w-full py-3 px-4 rounded-lg font-semibold transition-all bg-blue-500/20 hover:bg-blue-500/30 text-blue-300 border border-blue-500/30 mb-4">
                Refresh Logs
              </button>

              <div className="mt-6 space-y-3">
                <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wide">Configuration</h3>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Server IP:</span>
                    <span className="text-white font-mono text-sm">{serverConfig.serverIP}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Min Clients:</span>
                    <span className="text-white font-semibold">{serverConfig.minClientsRequired}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Method:</span>
                    <span className="text-purple-300 font-semibold">{serverConfig.aggregationMethod}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400 text-sm">Total Rounds:</span>
                    <span className="text-white font-semibold">{serverStats.totalRounds}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2">
            <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
              <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Client Activity Logs
              </h2>

              <div className="space-y-2 max-h-[500px] overflow-y-auto pr-2 custom-scrollbar">
                {clientLogs.length === 0 ? (
                  <div className="text-center py-12">
                    <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-3" />
                    <p className="text-slate-400">No client activity yet</p>
                    <p className="text-slate-500 text-sm mt-1">Logs will appear here when clients interact with the server</p>
                  </div>
                ) : (
                  clientLogs.map((log) => (
                    <div key={log.id} className={`p-4 rounded-lg border backdrop-blur-sm transition-all hover:scale-[1.01] ${
                      log.status === 'success' ? 'bg-green-500/10 border-green-500/30' :
                      log.status === 'error' ? 'bg-red-500/10 border-red-500/30' : 'bg-blue-500/10 border-blue-500/30'
                    }`}>
                      <div className="flex items-start justify-between">
                        <div className="flex items-start gap-3 flex-1">
                          <div className="mt-1">
                            {log.status === 'success' ? <CheckCircle className="w-5 h-5 text-green-400" /> :
                             log.status === 'error' ? <AlertCircle className="w-5 h-5 text-red-400" /> :
                             <Activity className="w-5 h-5 text-blue-400" />}
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-semibold text-white">{log.clientId}</span>
                              <span className="text-xs text-slate-400">{timeAgo(log.timestamp)}</span>
                            </div>
                            <p className="text-slate-300 text-sm">{log.message}</p>
                            <p className="text-xs text-slate-500 mt-1">{formatTimestamp(log.timestamp)}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .custom-scrollbar::-webkit-scrollbar { width: 8px; }
        .custom-scrollbar::-webkit-scrollbar-track { background: rgba(255, 255, 255, 0.05); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }
      `}</style>
    </div>
  );
};

export default ServerDashboard;
