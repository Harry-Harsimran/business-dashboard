
from flask import Flask, render_template
import db

app = Flask(__name__)


@app.route("/")
def overview():
    return render_template(
        "overview.html",
        active="overview",
        summary=db.get_summary(),
        monthly=db.get_monthly_metrics(),
    )


@app.route("/revenue")
def revenue():
    return render_template(
        "revenue.html",
        active="revenue",
        monthly=db.get_monthly_metrics(),
    )


@app.route("/profit")
def profit():
    return render_template(
        "profit.html",
        active="profit",
        monthly=db.get_monthly_metrics(),
    )


@app.route("/growth")
def growth():
    return render_template(
        "growth.html",
        active="growth",
        growth=db.get_growth_series(),
    )


@app.route("/kpis")
def kpis():
    return render_template(
        "kpis.html",
        active="kpis",
        kpis=db.get_kpis(),
    )


if __name__ == "__main__":
    app.run(debug=True)
