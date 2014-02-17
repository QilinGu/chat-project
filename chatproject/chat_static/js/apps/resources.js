// authentication resource
angular.module('authApp').factory('authService', function($http) {
    return {
        login: function(payload, successCallback, errorCallback){
            payload = angular.toJson(payload);
            $http.post('/api/v1/auth/login/session/', payload).then(successCallback, errorCallback)
        },
        register: function(payload, successCallback, errorCallback){
            payload = angular.toJson(payload);
            $http.post('/api/v1/account/', payload).then(successCallback, errorCallback)
        },
        logout: function(successCallback){
            $http.get('/api/v1/auth/logout/session/').success(successCallback);
        },
        forgot_password: function(payload, successCallback, errorCallback){
            payload = angular.toJson(payload);
            $http.put('/api/v1/auth/forgot/password/', payload).then(successCallback, errorCallback)
        },
        forgot_username: function(payload, successCallback, errorCallback){
            payload = angular.toJson(payload);
            $http.put('/api/v1/auth/forgot/username/', payload).then(successCallback, errorCallback)
        },
        new_password: function(payload, successCallback, errorCallback){
            payload = angular.toJson(payload);
            $http.put('/api/v1/auth/forgot/new-password/', payload).then(successCallback, errorCallback)
        }
    }
});

// Node Resource
angular.module('mainApp').factory('socket', function ($rootScope, $location) {
  var socket = io.connect('http://127.0.0.1:8080');
  return {
    on: function (eventName, callback) {
      socket.on(eventName, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          callback.apply(socket, args);
        });
      });
    },
    emit: function (eventName, data, callback) {
      socket.emit(eventName, data, function () {
        var args = arguments;
        $rootScope.$apply(function () {
          if (callback) {
            callback.apply(socket, args);
          }
        });
      })
    }
  };
});

// Chat Resource
angular.module('chatApp').factory('chatService', function($http){
    return {
        session: function(username, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/sessions/';
            $http.post(url).then(successCallback, errorCallback)
        },
        message: function(payload, username, uuid , successCallback, errorCallback){
            payload = angular.toJson(payload);
            var url = '/api/v1/account/' + username + '/sessions/' + uuid + '/messages/';
            $http.post(url, payload).then(successCallback, errorCallback)
        }
    }
});

// User Service
angular.module('chatApp').factory('accountService', function($http){
    return {
        check_follow: function(username, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/follow/';
            $http.get(url).then(successCallback, errorCallback);
        },
        follow: function(username, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/follow/';
            $http.post(url).then(successCallback, errorCallback);
        },
        unfollow: function(username, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/follow/';
            $http.delete(url).then(successCallback, errorCallback);
        },
        user_profile: function(username, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/';
            $http.get(url).then(successCallback, errorCallback);
        },
        follows: function(username, payload, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/follows/';
            $http.get(url, {params: payload}).then(successCallback, errorCallback);
        },
        update_profile: function(username, payload, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/';
            payload = angular.toJson(payload);
            $http.put(url, payload).then(successCallback, errorCallback);
        },
        change_password: function(username, payload, successCallback, errorCallback){
            var url = '/api/v1/account/' + username + '/change-password/';
            payload = angular.toJson(payload);
            $http.put(url, payload).then(successCallback, errorCallback);
        }
    }
});