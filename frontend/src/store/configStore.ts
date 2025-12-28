import { create } from 'zustand';
import type { BusinessConfig } from '../types/config';
import type { HumanAgent } from '../types/agent';

interface ConfigStore {
  businessConfigs: BusinessConfig[];
  agents: HumanAgent[];
  selectedBusinessId: string | null;
  setBusinessConfigs: (configs: BusinessConfig[]) => void;
  addBusinessConfig: (config: BusinessConfig) => void;
  updateBusinessConfig: (id: string, updates: Partial<BusinessConfig>) => void;
  removeBusinessConfig: (id: string) => void;
  setAgents: (agents: HumanAgent[]) => void;
  addAgent: (agent: HumanAgent) => void;
  updateAgent: (id: string, updates: Partial<HumanAgent>) => void;
  removeAgent: (id: string) => void;
  setSelectedBusiness: (id: string | null) => void;
}

export const useConfigStore = create<ConfigStore>((set) => ({
  businessConfigs: [],
  agents: [],
  selectedBusinessId: null,

  setBusinessConfigs: (configs) => set({ businessConfigs: configs }),

  addBusinessConfig: (config) =>
    set((state) => ({
      businessConfigs: [...state.businessConfigs, config],
    })),

  updateBusinessConfig: (id, updates) =>
    set((state) => ({
      businessConfigs: state.businessConfigs.map((config) =>
        config.id === id ? { ...config, ...updates } : config
      ),
    })),

  removeBusinessConfig: (id) =>
    set((state) => ({
      businessConfigs: state.businessConfigs.filter((config) => config.id !== id),
    })),

  setAgents: (agents) => set({ agents }),

  addAgent: (agent) =>
    set((state) => ({
      agents: [...state.agents, agent],
    })),

  updateAgent: (id, updates) =>
    set((state) => ({
      agents: state.agents.map((agent) =>
        agent.id === id ? { ...agent, ...updates } : agent
      ),
    })),

  removeAgent: (id) =>
    set((state) => ({
      agents: state.agents.filter((agent) => agent.id !== id),
    })),

  setSelectedBusiness: (id) => set({ selectedBusinessId: id }),
}));

