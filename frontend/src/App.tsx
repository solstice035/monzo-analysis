import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { Layout } from "@/components/layout";
import { Dashboard, Transactions, Budgets, Rules, Subscriptions, Settings } from "@/pages";

function NotFound() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
      <div
        className="text-8xl text-coral mb-4"
        style={{ fontFamily: "var(--font-display)" }}
      >
        404
      </div>
      <h1
        className="text-2xl text-white mb-2"
        style={{ fontFamily: "var(--font-display)" }}
      >
        PAGE NOT FOUND
      </h1>
      <p className="text-stone mb-6">The page you're looking for doesn't exist.</p>
      <Link
        to="/"
        className="px-6 py-2 bg-coral text-white rounded-full text-sm font-medium hover:bg-coral-bright transition-colors"
      >
        Back to Dashboard
      </Link>
    </div>
  );
}

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="transactions" element={<Transactions />} />
          <Route path="budgets" element={<Budgets />} />
          <Route path="rules" element={<Rules />} />
          <Route path="subscriptions" element={<Subscriptions />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
