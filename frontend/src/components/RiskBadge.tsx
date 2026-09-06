export default function RiskBadge({risk}:{risk:string}){return <span className={`risk ${risk.toLowerCase()}`}>{risk}</span>}
