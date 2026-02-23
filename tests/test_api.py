"""
Comprehensive tests for the Mergington High School Activities API
"""
import pytest


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_static(self, client):
        """Test that root path redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that getting activities returns 200 status"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that activities endpoint returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_has_correct_structure(self, client):
        """Test that each activity has the required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)
    
    def test_get_activities_includes_known_activities(self, client):
        """Test that response includes expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        assert "Soccer Team" in data
        assert "Basketball Club" in data
        assert "Drama Club" in data
        assert "Chess Club" in data


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup to an activity"""
        response = client.post(
            "/activities/Basketball Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]
        assert "Basketball Club" in data["message"]
    
    def test_signup_adds_participant(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newstudent@mergington.edu"
        client.post(f"/activities/Basketball Club/signup?email={email}")
        
        # Verify participant was added
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Basketball Club"]["participants"]
    
    def test_signup_invalid_activity(self, client):
        """Test signup to non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_signup_duplicate_participant(self, client):
        """Test that signing up twice returns an error"""
        email = "lucas@mergington.edu"
        response = client.post(f"/activities/Soccer Team/signup?email={email}")
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "already signed up" in data["detail"].lower()
    
    def test_signup_with_special_characters_in_name(self, client):
        """Test signup to activity with spaces and special characters"""
        response = client.post(
            "/activities/Math Olympiad/signup?email=mathwhiz@mergington.edu"
        )
        assert response.status_code == 200
    
    def test_signup_preserves_existing_participants(self, client):
        """Test that signing up doesn't remove existing participants"""
        # Soccer Team already has lucas@mergington.edu
        original_response = client.get("/activities")
        original_participants = original_response.json()["Soccer Team"]["participants"]
        
        # Add new participant
        client.post("/activities/Soccer Team/signup?email=newplayer@mergington.edu")
        
        # Verify both participants exist
        response = client.get("/activities")
        activities = response.json()
        participants = activities["Soccer Team"]["participants"]
        
        assert "lucas@mergington.edu" in participants
        assert "newplayer@mergington.edu" in participants
        assert len(participants) == len(original_participants) + 1


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        email = "lucas@mergington.edu"
        response = client.delete(
            f"/activities/Soccer Team/unregister?email={email}"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert "Soccer Team" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "lucas@mergington.edu"
        
        # Verify participant exists before unregistering
        response = client.get("/activities")
        activities = response.json()
        assert email in activities["Soccer Team"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Soccer Team/unregister?email={email}")
        
        # Verify participant was removed
        response = client.get("/activities")
        activities = response.json()
        assert email not in activities["Soccer Team"]["participants"]
    
    def test_unregister_invalid_activity(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "Activity not found" in data["detail"]
    
    def test_unregister_participant_not_signed_up(self, client):
        """Test unregistering a participant who isn't signed up returns 400"""
        email = "notsignedup@mergington.edu"
        response = client.delete(
            f"/activities/Basketball Club/unregister?email={email}"
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "not signed up" in data["detail"].lower()
    
    def test_unregister_preserves_other_participants(self, client):
        """Test that unregistering doesn't affect other participants"""
        # Chess Club has michael and daniel
        original_response = client.get("/activities")
        original_participants = original_response.json()["Chess Club"]["participants"]
        assert len(original_participants) == 2
        
        # Remove one participant
        client.delete("/activities/Chess Club/unregister?email=michael@mergington.edu")
        
        # Verify only one was removed
        response = client.get("/activities")
        activities = response.json()
        participants = activities["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" not in participants
        assert "daniel@mergington.edu" in participants
        assert len(participants) == 1
    
    def test_unregister_and_signup_again(self, client):
        """Test that a participant can unregister and then signup again"""
        email = "lucas@mergington.edu"
        activity = "Soccer Team"
        
        # Unregister
        response = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()[activity]["participants"]
        
        # Signup again
        response = client.post(f"/activities/{activity}/signup?email={email}")
        assert response.status_code == 200
        
        # Verify added back
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]


class TestEndToEndScenarios:
    """Integration tests for complete user workflows"""
    
    def test_multiple_signups_different_activities(self, client):
        """Test that a student can sign up for multiple activities"""
        email = "multitasker@mergington.edu"
        
        # Sign up for multiple activities
        client.post(f"/activities/Basketball Club/signup?email={email}")
        client.post(f"/activities/Drama Club/signup?email={email}")
        client.post(f"/activities/Art Workshop/signup?email={email}")
        
        # Verify participant in all activities
        response = client.get("/activities")
        activities = response.json()
        
        assert email in activities["Basketball Club"]["participants"]
        assert email in activities["Drama Club"]["participants"]
        assert email in activities["Art Workshop"]["participants"]
    
    def test_activity_participant_count(self, client):
        """Test that participant counts are accurate"""
        # Add participants to Basketball Club (starts empty)
        emails = [f"student{i}@mergington.edu" for i in range(5)]
        
        for email in emails:
            response = client.post(f"/activities/Basketball Club/signup?email={email}")
            assert response.status_code == 200
        
        # Verify count
        response = client.get("/activities")
        activities = response.json()
        assert len(activities["Basketball Club"]["participants"]) == 5
    
    def test_empty_activity_participants(self, client):
        """Test that some activities start with no participants"""
        response = client.get("/activities")
        activities = response.json()
        
        # Basketball Club should start empty
        assert len(activities["Basketball Club"]["participants"]) == 0
        assert isinstance(activities["Basketball Club"]["participants"], list)
