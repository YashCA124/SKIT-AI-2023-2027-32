from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from models import UserType

# HTTPBearer automatically handles extracting the token from the "Authorization: Bearer <token>" header.
# It also naturally ignores OPTIONS requests when configured properly with FastAPI's CORSMiddleware.
security = HTTPBearer()

# Replace with your actual secret key and algorithm settings
SECRET_KEY = "your-secret-key"
ALGORITHM = "HS256"

def require_role(required_role: UserType):
    """
    FastAPI dependency that enforces role-based access control using JWT claims.
    Usage in a route: @app.get("/endpoint", dependencies=[Depends(role_required(UserType.ADMIN))])
    """
    def role_checker(credentials: HTTPAuthorizationCredentials = Depends(security)):
        token = credentials.credentials
        
        try:
            # Decode the token to extract the claims (payload)
            claims = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )

        # Verify the role matches the required role's value
        if claims.get("role") != required_role.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden"
            )
            
        # Returning claims allows the endpoint to use the token payload if needed
        # e.g., current_user_claims: dict = Depends(role_required(UserType.PARKING_USER))
        return claims 

    return role_checker