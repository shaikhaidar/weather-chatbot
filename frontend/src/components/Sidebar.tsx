const Sidebar = ({ currentView, setCurrentView }: { currentView: string, setCurrentView: (view: string) => void }) => {
  const views = ['Chat', 'Raw Dataset', 'Conversation History', 'Settings'];

  return (
    <div className="w-64 bg-gray-900 text-white h-full flex flex-col">
      <div className="p-4 text-2xl font-bold border-b border-gray-700">
        weatherBOT
      </div>
      <div className="flex-1 overflow-y-auto">
        {views.map((view) => (
          <button
            key={view}
            onClick={() => setCurrentView(view)}
            className={`w-full text-left px-4 py-3 hover:bg-gray-800 transition-colors ${
              currentView === view ? 'bg-gray-800 border-l-4 border-blue-500' : ''
            }`}
          >
            {view}
          </button>
        ))}
      </div>
    </div>
  );
};

export default Sidebar;
