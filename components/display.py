import streamlit as st


def render_summary(summary: dict) -> None:
    """Affiche le résumé structuré retourné par le LLM."""

    if not summary:
        return

    # En-tête
    titre = summary.get("titre_reunion") or "Réunion sans titre"
    date = summary.get("date")
    duree = summary.get("duree_estimee")

    meta_parts = []
    if date:
        meta_parts.append(f"Date : {date}")
    if duree:
        meta_parts.append(f"Durée : {duree}")

    st.markdown(f"## {titre}")
    if meta_parts:
        st.caption(" · ".join(meta_parts))

    st.divider()

    # Participants
    participants = summary.get("participants") or []
    if participants:
        with st.expander("Participants", expanded=False):
            st.write(", ".join(participants))

    # Ordre du jour
    ordre = summary.get("ordre_du_jour") or []
    if ordre:
        with st.expander("Ordre du jour", expanded=False):
            for item in ordre:
                st.markdown(f"- {item}")

    # Points clés
    points = summary.get("points_cles") or []
    if points:
        st.subheader("Points clés")
        for point in points:
            st.markdown(f"- {point}")

    col1, col2 = st.columns(2)

    # Décisions
    decisions = summary.get("decisions") or []
    with col1:
        st.subheader(f"Décisions ({len(decisions)})")
        if decisions:
            for d in decisions:
                decision_text = d.get("decision", "")
                contexte = d.get("contexte")
                st.markdown(f"**{decision_text}**")
                if contexte:
                    st.caption(contexte)
                st.markdown("")
        else:
            st.caption("Aucune décision formelle.")

    # Actions
    actions = summary.get("actions") or []
    with col2:
        st.subheader(f"Actions ({len(actions)})")
        if actions:
            priority_color = {"haute": "🔴", "moyenne": "🟡", "basse": "🟢"}
            for a in actions:
                action_text = a.get("action", "")
                responsable = a.get("responsable")
                deadline = a.get("deadline")
                priorite = (a.get("priorite") or "basse").lower()

                icon = priority_color.get(priorite, "⚪")
                label_parts = [f"{icon} {action_text}"]
                meta = []
                if responsable:
                    meta.append(f"**{responsable}**")
                if deadline:
                    meta.append(f"avant le {deadline}")
                st.markdown(" · ".join(label_parts))
                if meta:
                    st.caption(" — ".join(meta))
                st.markdown("")
        else:
            st.caption("Aucune action identifiée.")

    # Prochaine réunion
    prochaine = summary.get("prochaine_reunion")
    if prochaine:
        st.divider()
        st.info(f"Prochaine réunion : {prochaine}")
