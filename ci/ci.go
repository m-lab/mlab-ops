package ci

import (
	"appengine"
	"encoding/json"
	"io/ioutil"
	"net/http"
)

func init() {
	http.HandleFunc("/", handler)
}

var expected_user_agent string = "Google Code Project Hosting (+http://code.google.com/p/support/wiki/PostCommitWebHooks)"

func handler(w http.ResponseWriter, r *http.Request) {
	//redirect_map := map[string]string {
	//	"libraries": "https://drone.io/dominic-mlab/m-lab.libraries?key=BV8KN727SQ1JMEK7DKIGSO97SLBDJL2O",
	//	"ns": "https://drone.io/dominic-mlab/m-lab.ns?key=S4MHVE51D5KN5SGK1IOV1TA0SGK21RBF",
	//}

	if r.Method == "POST" {
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
		c.Debugf("Repository: %s", m["repository_path"])
		// TODO: post to drone.io based on contents
		//http.Redirect(w, r, redirect_map["libraries"], http.StatusFound)
	}
}
