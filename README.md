# BahaMap

Who in Metro Manila lives in harm's way when the floods come?

BahaMap is a flood-exposure atlas covering all ~1,700 barangays of the National Capital Region. It crosses Project NOAH flood hazard maps (5-, 25-, and 100-year scenarios) with official PSGC barangay boundaries, 2020 census population data, and OpenStreetMap facility locations to compute an exposure score for every barangay. The result ships as an interactive Streamlit app with plain-language briefs in English and Tagalog.

## Status

Started August 24, 2026. The design spec and the 17-task implementation plan are in `docs/superpowers/`. Currently in week 1: data foundation. Target launch: September 20, 2026.

- Week 1 (Aug 24-30): data acquisition and cleaning
- Week 2 (Aug 31-Sep 6): exposure analysis
- Week 3 (Sep 7-13): Streamlit app, deployment, bilingual briefs
- Week 4 (Sep 14-20): polish and launch

## How it's built

I'm building this solo, with Claude Code as the primary development tool: design spec first, then a reviewed implementation plan, then task-by-task execution with commit checkpoints. All analysis is precomputed offline so the deployed app serves static data (<100 MB) and stays fast and free to host.
