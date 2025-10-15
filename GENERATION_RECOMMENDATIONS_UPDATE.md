# Generation Recommendations Feature - Implementation Summary

## Overview
Added a recommendation system that helps users understand which files they should upload to their website based on the size and complexity of their site.

## Bug Fixes Applied
1. **Fixed missing total_pages**: Added `count_pages_in_directory()` function to count markdown files and store the count in the generation record
2. **Added website name display**: Updated API and frontend to show website name instead of just generation ID on the generations page

## Changes Made

### Backend Changes

#### 1. New Utility Module: `backend/app/utils/recommendations.py`
- Created recommendation logic function `get_file_recommendation()`
- Implements the following rules:
  - **Minimal** (≤50 pages, <2MB): Just `llms.txt`
  - **Standard** (50-500 pages, <10MB): `llms.txt` + `llms-full.txt`
  - **Complete** (>500 pages or ≥10MB): `llms.txt` + folder structure
- Returns recommendation object with:
  - Type (minimal/standard/complete)
  - Title and description
  - List of recommended files
  - Reason explaining why these files are recommended

#### 2. Schema Updates: `backend/app/schemas/generation.py`
- Added `FileRecommendation` schema with fields:
  - `type`: Literal["minimal", "standard", "complete"]
  - `title`: str
  - `description`: str
  - `files`: List[str]
  - `reason`: str
- Updated `GenerationResponse` to include optional `recommendation` field
- Updated `GenerationStatusResponse` to include optional `recommendation` field

#### 3. Generation Task Updates: `backend/app/tasks/generation.py`
- Added `count_pages_in_directory()` function to count markdown pages
- Updated generation completion logic to:
  - Count total pages from generated markdown files
  - Store `total_pages` in the generation record
  - This enables recommendation calculation

#### 4. API Updates: `backend/app/api/v1/generations.py`
- Imported recommendation utility function
- Updated `/history` endpoint to:
  - Join with Website table to get website name and URL
  - Calculate and include recommendations for completed generations
  - Include website information in responses
- Updated `/{generation_id}` endpoint to calculate and include recommendation for completed generations
- Recommendations are only calculated when generation is completed and has both `total_pages` and `file_size`

### Frontend Changes

#### 1. Type Definitions: `frontend/src/types/index.ts`
- Added `RecommendationType` type
- Added `FileRecommendation` interface
- Updated `Generation` interface to include:
  - `website_name?: string`
  - `website_url?: string`
  - `total_pages?: number`
  - `recommendation?: FileRecommendation`

#### 2. New Component: `frontend/src/components/RecommendationCard.tsx`
- Displays recommendation summary in a card format
- Shows stats (total pages and file size)
- Lists recommended files with checkmarks
- Includes button to view detailed deployment instructions
- Color-coded badges based on recommendation type:
  - Minimal: Green
  - Standard: Blue
  - Complete: Purple

#### 3. New Component: `frontend/src/components/DeploymentTipsModal.tsx`
- Modal dialog with comprehensive deployment instructions
- Explains why specific files are recommended
- Provides step-by-step deployment guide:
  1. Download files
  2. Extract ZIP
  3. Select recommended files
  4. Upload to website root
- Includes important notes about file accessibility and testing

#### 4. Page Updates: `frontend/src/pages/GenerationsPage.tsx`
- Integrated `RecommendationCard` component
- Integrated `DeploymentTipsModal` component
- Added state management for modal visibility
- Shows recommendation card for completed generations with available data
- Displays modal when user clicks "View Deployment Instructions"
- Updated generation card header to show:
  - Website name as the title (instead of generation ID)
  - Generation ID in the description area
  - Status badge with improved layout

### Testing

#### Test File: `backend/test_recommendations.py`
Created comprehensive tests covering:
- Minimal setup (30 pages, 1.5MB)
- Standard setup (200 pages, 5MB)
- Complete setup with many pages (600 pages, 8MB)
- Complete setup with large file (100 pages, 12MB)
- Edge cases (50 pages, exactly 2MB)

All tests pass successfully ✅

## Features Implemented

### ✅ Recommendation Logic
- Simple function that evaluates page count and file size
- Returns one of three recommendations based on defined thresholds

### ✅ UI After Generation
- Stats summary card showing pages and size
- One-line recommendation about which files to upload
- Button to see detailed deployment tips

### ✅ Deployment Tips Modal
- Explains why specific files are recommended for their site
- Step-by-step deployment instructions
- Clear note that recommendations are suggestions (users can upload what they want)

### ✅ API Response Integration
- Recommendations automatically calculated and included in API responses
- Only added for completed generations with available metrics

## User Experience Flow

1. User completes a generation
2. Generation list shows completed status
3. User sees a "Deployment Recommendation" card with:
   - Website stats (pages, size)
   - Recommended setup type (minimal/standard/complete)
   - List of files to upload
4. User clicks "View Deployment Instructions" button
5. Modal opens with:
   - Detailed explanation of why these files are recommended
   - Step-by-step deployment guide
   - Important notes and best practices
6. User follows instructions to deploy their LLM-ready files

## Files Modified

### Backend
- `backend/app/utils/recommendations.py` (new)
- `backend/app/schemas/generation.py`
- `backend/app/api/v1/generations.py`
- `backend/app/tasks/generation.py`
- `backend/test_recommendations.py` (new)

### Frontend
- `frontend/src/types/index.ts`
- `frontend/src/components/RecommendationCard.tsx` (new)
- `frontend/src/components/DeploymentTipsModal.tsx` (new)
- `frontend/src/pages/GenerationsPage.tsx`

## Next Steps

To see the feature in action:
1. Ensure backend server is running
2. Ensure frontend dev server is running
3. Complete a generation for a website
4. View the generations page to see the recommendation card
5. Click "View Deployment Instructions" to see the full modal

## Notes

- Recommendations are calculated on-the-fly based on generation metrics
- No database changes required
- Backward compatible - existing generations without metrics won't show recommendations
- The feature gracefully handles missing data (recommendation only shows when data is available)