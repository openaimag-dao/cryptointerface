import { create } from "zustand";

export type ConnectionStatus = "online" | "connecting" | "offline";

interface ConnectionState {
  apiStatus: ConnectionStatus;
  wsStatus: ConnectionStatus;
  setApiStatus: (status: ConnectionStatus) => void;
  setWsStatus: (status: ConnectionStatus) => void;
}

export const useConnectionStore = create<ConnectionState>((set) => ({
  apiStatus: "connecting",
  wsStatus: "connecting",
  setApiStatus: (status) => set({ apiStatus: status }),
  setWsStatus: (status) => set({ wsStatus: status }),
}));
