from app.services.traveller_service import TravellerRepository, TravellerService

# Module-level singletons — shared across all requests in the same process.
# Replaced by proper DI + DB session in Sprint 2.
_repository = TravellerRepository()
traveller_service = TravellerService(_repository)
