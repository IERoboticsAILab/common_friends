import requests
import json
from collections import deque

################################################################################
# 1) API CONFIGURATION
################################################################################
API_HOST = "instagram-scraper-api2.p.rapidapi.com"
API_KEY = "0acf61faf2msh0b14d26175218ffp167e2cjsn3492bbf87bc2"

HEADERS = {
    "x-rapidapi-host": API_HOST,
    "x-rapidapi-key": API_KEY
}

################################################################################
# 2) PAGINATED REQUESTS - FETCH ALL FOLLOWERS
################################################################################
def fetch_followers(user):
    """
    Returns *all* followers for `user`, handling pagination in batches of up to 1000.
    """
    # First request: get the total follower count with amount=1
    url = f"https://{API_HOST}/v1/followers?username_or_id_or_url={user}&amount=1"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    total_followers = data["data"]["count"]  # total number of followers
    all_followers = []
    pagination_token = ""
    
    remaining = total_followers
    while remaining > 0:
        batch_size = min(remaining, 1000)
        
        if pagination_token:
            url = (
                f"https://{API_HOST}/v1/followers?username_or_id_or_url={user}"
                f"&amount={batch_size}&pagination_token={pagination_token}"
            )
        else:
            url = f"https://{API_HOST}/v1/followers?username_or_id_or_url={user}&amount={batch_size}"
        
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        resp_data = resp.json()

        
        data_obj = resp_data.get("data", {})
        items_list = data_obj.get("items", [])
        
        # Add followers
        for item in items_list:
            username = item.get("username")
            if username:
                all_followers.append(username)
        
        # Update pagination token
        pagination_token = resp_data.get("pagination_token", "")
        remaining -= batch_size
        
        # If no more pagination token is provided and we've requested less than 1000, we're done
        if not pagination_token and batch_size < 1000:
            break
    
    return all_followers

################################################################################
# 3) PAGINATED REQUESTS - FETCH ALL FOLLOWINGS
################################################################################
def fetch_followings(user):
    """
    Returns *all* accounts that `user` follows, handling pagination in batches of up to 1000.
    """
    # First request: get the total 'followed' count with amount=1
    url = f"https://{API_HOST}/v1/following?username_or_id_or_url={user}&amount=1"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()
    data = response.json()
    
    total_followings = data["data"]["count"]  # total number of followings
    all_followings = []
    pagination_token = ""
    
    remaining = total_followings
    while remaining > 0:
        batch_size = min(remaining, 1000)
        
        if pagination_token:
            url = (
                f"https://{API_HOST}/v1/following?username_or_id_or_url={user}"
                f"&amount={batch_size}&pagination_token={pagination_token}"
            )
        else:
            url = f"https://{API_HOST}/v1/following?username_or_id_or_url={user}&amount={batch_size}"
        
        resp = requests.get(url, headers=HEADERS)
        resp.raise_for_status()
        resp_data = resp.json()
        data_obj = resp_data.get("data", {})
        items_list = data_obj.get("items", [])
        
        # Add followers
        for item in items_list:
            username = item.get("username")
            if username:
                all_followings.append(username)
        
        # Update pagination token
        pagination_token = resp_data.get("pagination_token", "")
        remaining -= batch_size
        
        if not pagination_token and batch_size < 1000:
            break
    
    return all_followings

################################################################################
# 4) DETERMINE MUTUAL FRIENDS
################################################################################
def get_mutual_friends(user):
    """
    Returns a set of users who both follow `user` AND are followed by `user`.
    """
    followers = set(fetch_followers(user))
    followings = set(fetch_followings(user))
    return followers.intersection(followings)

################################################################################
# 5) BFS TO FIND SHORTEST "MUTUAL-FRIEND" DISTANCE
################################################################################
def mutual_connection_distance(user1, user2, max_depth):
    """
    Returns the minimum number of 'mutual-friend hops' between user1 and user2.
      - 0 if user1 == user2
      - 1 if user2 is a direct mutual friend of user1
      - etc.
      - The path is also returned as a list of usernames, displayed by joining the elements with ' -> '.
    If no connection is found within `max_depth`, returns None.
    """
    if user1 == user2:
        return 0
    
    visited = set([user1])
    queue = deque([(user1, 0)])  # (current_user, distance)
    predecessors = {user1: None}
    
    while queue:
        current_user, distance = queue.popleft()
        
        # If we've reached the max search depth, don't go further
        if distance >= max_depth:
            continue
        
        # Get current user's mutual friends
        current_mutuals = get_mutual_friends(current_user)
        
        if user2 in current_mutuals:
            path = [user2]
            while current_user is not None:
                path.append(current_user)
                current_user = predecessors[current_user]
            return distance + 1, path[::-1] # Return distance and path
        
        # Enqueue each mutual friend for further exploration
        for mf in current_mutuals:
            if mf not in visited:
                visited.add(mf)
                queue.append((mf, distance + 1))
                predecessors[mf] = current_user
    
    # No connection found up to max_depth
    return None, None

################################################################################
# 6) EXAMPLE USAGE
################################################################################
if __name__ == "__main__":
    # Replace these with actual usernames you want to test
    user1 = "leslieramirez21311"
    user2 = "liu_kevin5"

    distance = mutual_connection_distance(user1, user2, max_depth=3)
    
    if distance is None:
        print(f"No mutual-friend connection found between {user1} and {user2} (depth <= 3).")
    elif distance == 0:
        for users in distance:
            print(f"{user1} and {user2} are the same user.")
    else:
        print(f"{user1} is {distance[0]} mutual-friend hop(s) away from {user2}. \n Path: {' -> '.join(distance[1])}")



