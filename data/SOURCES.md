# Data Sources and Provenance

## IEEE RTS-GMLC Repository

- **Repository:** `https://github.com/GridMod/RTS-GMLC`
- **Branch:** `master`
- **Commit SHA:** `3ece0d3725c844056132393ee252b3083dd4eab4`
- **Commit Timestamp (UTC):** `2025-10-23T02:33:26Z`
- **Download Date:** `2026-11-21`
- **Citation:** C. Barrows et al., "The IEEE Reliability Test System: A Proposed 2019 Update," *IEEE Transactions on Power Systems*, vol. 35, no. 1, pp. 119–127, Jan. 2020. DOI: `10.1109/TPWRS.2019.2925557`.

### Local Files

1. `data/gen.csv`
   - **Upstream Path:** `RTS_Data/SourceData/gen.csv`
   - **Raw URL:** `https://raw.githubusercontent.com/GridMod/RTS-GMLC/3ece0d3725c844056132393ee252b3083dd4eab4/RTS_Data/SourceData/gen.csv`
   - **Size / Rows:** 32,451 bytes / 158 generating units (excluding header)
   - **SHA256:** `988466f29132b73739de60c9204dd4a2a9ceb0adf572e5966c086611272f4068`
   - **Fields Used:** `GEN UID`, `Bus ID` (first digit identifies Area 1, 2, or 3), `Unit Group`, `Unit Type`, `Fuel`, `PMax MW`, `MTTF Hr`, `MTTR Hr`, `FOR`.

2. `data/REAL_TIME_regional_Load.csv`
   - **Upstream Path:** `RTS_Data/timeseries_data_files/Load/REAL_TIME_regional_Load.csv`
   - **Raw URL:** `https://raw.githubusercontent.com/GridMod/RTS-GMLC/3ece0d3725c844056132393ee252b3083dd4eab4/RTS_Data/timeseries_data_files/Load/REAL_TIME_regional_Load.csv`
   - **Size / Rows:** 5,181,939 bytes / 105,408 five-minute intervals (columns: `Year`, `Month`, `Day`, `Period`, `1`, `2`, `3`)
   - **SHA256:** `462888ae357239ec63bd22b96863900259a9849743df0ca6711ceb5a6d53da57`
   - **Purpose:** Area peak-load context only (Area 1/2/3 peak load = 2,850.0 MW).

## Technical and Economic Reference Documents

3. **GE Vernova GER-3620 Rev P**
   - **Title:** *Heavy-Duty Gas Turbine Operating and Maintenance Considerations*
   - **Authors:** D. Beagle, B. Moran, M. McDufford, M. Merine (GE Vernova, Atlanta, GA)
   - **Release Date:** 2021-03-15 (Rev P, 01/21)
   - **URL:** `https://www.gevernova.com/content/dam/gepower-new/global/en_US/downloads/gas-new-site/resources/reference/GER-3620-P.pdf`
   - **Verified On:** `2026-11-21`

4. **U.S. EIA AEO 2026 Electricity Market Module Assumptions**
   - **Title:** *Assumptions to the Annual Energy Outlook 2026: Electricity Market Module*
   - **Publisher / Date:** U.S. Energy Information Administration, April 2026
   - **URL:** `https://www.eia.gov/outlooks/aeo/assumptions/pdf/EMM_Assumptions.pdf`
   - **Table Used:** Table 3 (doc p. 6 / PDF p. 12), Fixed O&M and Variable O&M (2025 dollars) for aeroderivative and industrial-frame combustion turbines.
   - **Verified On:** `2026-11-21`
