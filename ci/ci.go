package ci

import (
	"appengine"
	"appengine/urlfetch"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"strings"
)

func init() {
	http.HandleFunc("/", handler)
}

var expected_user_agent string = "Google Code Project Hosting (+http://code.google.com/p/support/wiki/PostCommitWebHooks)"
var repository_path_prefix string = "https://code.google.com/p/m-lab."
var drone_io_prefix string = "https://drone.io/dominic-mlab/m-lab."

func handler(w http.ResponseWriter, r *http.Request) {
	if r.Method == "POST" {
		redirect_map := map[string]string {
			"libraries": "BV8KN727SQ1JMEK7DKIGSO97SLBDJL2O",
			"ns":        "S4MHVE51D5KN5SGK1IOV1TA0SGK21RBF",
			"pipeline":  "6MO0BPE3RKNHJ1EOS3MHE89M71C9JF8M",
		}

		c := appengine.NewContext(r)
		c.Debugf("Request: %#v", r)

		if r.Header["User-Agent"][0] != expected_user_agent {
			c.Errorf("Unexpected user agent: %v", r.Header["User-Agent"])
			http.Error(w, "Unexpected user agent", http.StatusForbidden)
			return
		}

		var b []byte;
		b, err := ioutil.ReadAll(r.Body)
		r.Body.Close()

		if err != nil {
			c.Errorf("Failed to read body: %v", err)
			return
		}
		c.Debugf("Body: %s", string(b))
		var f interface{}
		err = json.Unmarshal(b, &f)
		if err != nil {
			c.Errorf("Failed to unmarshal body: %s", string(b))
			return
		}
		m := f.(map[string]interface{})
		repository_path := m["repository_path"].(string)
		c.Debugf("Repository: %s", repository_path)

		if !strings.HasPrefix(repository_path, repository_path_prefix) {
			c.Errorf("Unexpected repository path: %s", repository_path)
			return
		}
		repo := repository_path[len(repository_path_prefix):len(repository_path)-1]
		var key string
		var exists bool
		if key, exists = redirect_map[repo]; !exists {
			c.Warningf("No redirect for repo %s", repo)
			return
		}

		c.Infof("Found key %s for repo %s", key, repo)
		var url string = drone_io_prefix + repo + "?key=" + key

		// post to drone.io based on contents
		c.Infof("Forwarding request to %s", url)
		client := urlfetch.Client(c)
		resp, err := client.Post(url, repo, nil)
		if err != nil {
			c.Errorf("Error posting: %s", err)
			fmt.Fprint(w, "Error posting: %s", err)
			return
		}

		body, _ := ioutil.ReadAll(resp.Body)
		resp.Body.Close()
		c.Infof("POST response: %s", body)
		fmt.Fprint(w, "POST response: %s", body)
	}
}
