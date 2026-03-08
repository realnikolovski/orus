from pages.analysis import render as render_analysis
from pages.dashboard import render as render_dashboard
from pages.data import render as render_data
from pages.holdings import render as render_holdings
from pages.portfolio import render as render_portfolio
from pages.rebalancing import render as render_rebalancing
from pages.weights import render as render_weights

PAGE_RENDERERS = {
    "Dashboard": render_dashboard,
    "Portfolio": render_portfolio,
    "Daten": render_data,
    "Analyse": render_analysis,
    "Gewichte": render_weights,
    "Investiert": render_holdings,
    "Rebalancing": render_rebalancing,
}
