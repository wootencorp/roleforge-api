"""
Character schemas for request/response validation.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, validator


class AbilityScores(BaseModel):
    """Schema for D&D 5e ability scores."""
    strength: int = Field(..., ge=1, le=30)
    dexterity: int = Field(..., ge=1, le=30)
    constitution: int = Field(..., ge=1, le=30)
    intelligence: int = Field(..., ge=1, le=30)
    wisdom: int = Field(..., ge=1, le=30)
    charisma: int = Field(..., ge=1, le=30)


class CharacterBase(BaseModel):
    """Base character schema."""
    name: str = Field(..., min_length=1, max_length=100)
    race: str = Field(..., min_length=1, max_length=50)
    character_class: str = Field(..., min_length=1, max_length=50, alias="class")
    level: int = Field(default=1, ge=1, le=20)
    background: str = Field(..., min_length=1, max_length=50)
    alignment: str = Field(..., min_length=1, max_length=50)
    ability_scores: AbilityScores
    hit_points: int = Field(..., ge=1, le=1000)
    armor_class: int = Field(..., ge=1, le=30)
    experience_points: int = Field(default=0, ge=0)
    skills: List[str] = Field(default_factory=list)
    equipment: List[str] = Field(default_factory=list)
    spells: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None, max_length=5000)
    avatar_url: Optional[str] = None
    
    class Config:
        populate_by_name = True


class CharacterCreate(CharacterBase):
    """Schema for character creation."""
    use_ai: bool = Field(default=False)
    ai_prompt: Optional[str] = Field(None, max_length=1000)
    
    @validator('ai_prompt')
    def validate_ai_prompt(cls, v, values):
        if values.get('use_ai') and not v:
            raise ValueError('AI prompt is required when using AI generation')
        return v


class CharacterUpdate(BaseModel):
    """Schema for character updates."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    level: Optional[int] = Field(None, ge=1, le=20)
    hit_points: Optional[int] = Field(None, ge=1, le=1000)
    armor_class: Optional[int] = Field(None, ge=1, le=30)
    experience_points: Optional[int] = Field(None, ge=0)
    skills: Optional[List[str]] = None
    equipment: Optional[List[str]] = None
    spells: Optional[List[str]] = None
    notes: Optional[str] = Field(None, max_length=5000)
    avatar_url: Optional[str] = None


class CharacterResponse(CharacterBase):
    """Schema for character response."""
    id: str
    user_id: str
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class CharacterListResponse(BaseModel):
    """Schema for character list response."""
    characters: List[CharacterResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class CharacterGenerationRequest(BaseModel):
    """Schema for AI character generation request."""
    prompt: str = Field(..., min_length=10, max_length=1000)
    race: Optional[str] = Field(None, max_length=50)
    character_class: Optional[str] = Field(None, max_length=50, alias="class")
    level: int = Field(default=1, ge=1, le=20)
    include_backstory: bool = Field(default=True)
    include_artwork: bool = Field(default=False)
    
    class Config:
        populate_by_name = True


class CharacterGenerationResponse(BaseModel):
    """Schema for AI character generation response."""
    character: CharacterBase
    backstory: Optional[str] = None
    artwork_url: Optional[str] = None
    generation_metadata: Dict = Field(default_factory=dict)


class CharacterStats(BaseModel):
    """Schema for character statistics."""
    total_characters: int
    characters_by_class: Dict[str, int]
    characters_by_race: Dict[str, int]
    characters_by_level: Dict[str, int]
    average_level: float


class CharacterFilter(BaseModel):
    """Schema for character filtering."""
    search: Optional[str] = Field(None, max_length=100)
    race: Optional[str] = Field(None, max_length=50)
    character_class: Optional[str] = Field(None, max_length=50, alias="class")
    level_min: Optional[int] = Field(None, ge=1, le=20)
    level_max: Optional[int] = Field(None, ge=1, le=20)
    sort_by: str = Field(default="name")
    sort_order: str = Field(default="asc")
    page: int = Field(default=1, ge=1)
    per_page: int = Field(default=20, ge=1, le=100)
    
    @validator('sort_by')
    def validate_sort_by(cls, v):
        allowed_fields = ['name', 'level', 'race', 'class', 'created_at', 'updated_at']
        if v not in allowed_fields:
            raise ValueError(f'sort_by must be one of: {", ".join(allowed_fields)}')
        return v
    
    @validator('sort_order')
    def validate_sort_order(cls, v):
        if v not in ['asc', 'desc']:
            raise ValueError('sort_order must be "asc" or "desc"')
        return v
    
    @validator('level_max')
    def validate_level_range(cls, v, values):
        if v is not None and 'level_min' in values and values['level_min'] is not None:
            if v < values['level_min']:
                raise ValueError('level_max must be greater than or equal to level_min')
        return v
    
    class Config:
        populate_by_name = True

