import plotly.express as px


def create_bubble_chart(df, max_bubbles=5):
    """Crea un grafico a bolle interattivo con le top notizie trending."""
    top = df.nlargest(max_bubbles, "trend_score")

    fig = px.scatter(
        top,
        x="interactions",
        y="trend_score",
        size="trend_score",
        color="category",
        hover_name="title",
        hover_data={"source": True, "interactions": True, "trend_score": ":.0f"},
        size_max=80,
        template="plotly_white",
        labels={
            "interactions": "Volume Interazioni",
            "trend_score": "Indice di Tendenza",
            "category": "Categoria"
        },
        color_discrete_sequence=px.colors.qualitative.Set2
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e2e8f0"),
        height=450,
        xaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
        yaxis=dict(gridcolor="rgba(255,255,255,0.06)"),
    )
    return fig