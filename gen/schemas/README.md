# D&D 5e Modular Schema System

This directory contains the modular JSON schemas for the D&D 5e encounter generation and combat system. The schemas have been separated from the monolithic `gs_schema.json` to provide better organization, maintainability, and context window optimization.

## Schema Files

### `character_schema.json`
- **Purpose**: Defines the structure for individual character data (both players and NPCs)
- **Content**: **EXACT COPY** of the character object structure from `gs_schema.json`
- **Includes**: All character properties, data types, validation rules, and values
- **Additional Fields**: `is_enemy` and `ai_type` for NPCs
- **Usage**: Used for character generation, validation, and data consistency

### `encounter_schema.json`
- **Purpose**: Defines encounter-specific data including battlefield layout and positioning
- **Content**: Battlefield dimensions, terrain features, starting positions for all participants
- **Fixed Battlefield**: 100x100 grid (5 feet per unit) for interface compatibility
- **Usage**: Used for encounter generation, tactical positioning, and combat initialization

## Key Features

### Fixed Battlefield Dimensions
- **Grid Size**: 100x100 units
- **Unit Scale**: 5 feet per grid unit
- **Total Area**: 500x500 feet
- **Rationale**: Maintains compatibility with existing interfaces while providing sufficient tactical space

### Tactical Positioning
- **Player Positions**: Starting locations for player characters
- **NPC Positions**: Starting locations for NPCs with enemy/friendly designation
- **Facing Direction**: 8-directional facing for tactical orientation
- **Position Notes**: Additional context for positioning decisions

### Terrain Features
- **Cover Types**: Full, three-quarters, half cover
- **Movement Effects**: Difficult terrain, hazards, elevation
- **Environmental Effects**: Weather, lighting, water features
- **Damage Hazards**: Dangerous terrain that can harm characters

### Data Separation Benefits
- **Context Optimization**: Send only relevant schema data to LLM APIs
- **Maintainability**: Easier to update individual schema components
- **Reusability**: Character schema can be used independently
- **Validation**: Separate validation for different data types

## Integration

### Character Generation
- Uses `character_schema.json` for individual character creation
- Ensures data consistency across players and NPCs
- Maintains all existing character properties and validation

### Encounter Generation
- Uses `encounter_schema.json` for battlefield layout and positioning
- Integrates with existing lore and NPC generation
- Provides tactical positioning for both sides

### Combat Engine
- Loads encounter data from `encounter.json`
- Applies AI-generated positions with graceful fallback
- Maintains existing random positioning as backup

## File Organization

```
schemas/
├── character_schema.json      # Character data structure
├── encounter_schema.json      # Encounter layout and positioning
├── character_schema.min.json  # Minified version for API calls
├── encounter_schema.min.json  # Minified version for API calls
└── README.md                  # This documentation
```

## Non-Breaking Changes

- **Existing Files**: `gs_schema.json` and `gs_schema.min.json` remain **UNCHANGED**
- **Additive Features**: New schemas add functionality without disrupting existing systems
- **Backward Compatibility**: All existing encounter generation and combat functionality preserved
- **Graceful Degradation**: Systems fall back to existing behavior if new features unavailable

## Next Steps

1. **Schema Validation**: Ensure new schemas validate existing data correctly
2. **Generation Logic**: Update encounter generation to use new schemas
3. **Combat Integration**: Modify combat engine to load encounter positioning
4. **Testing**: Validate interface compatibility and system integration
5. **Documentation**: Update combat engine readme with new features 