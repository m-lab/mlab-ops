package ci

import (
	"appengine"
	"io/ioutil"
	//"json"
	"net/http"
)

func init() {
	http.HandleFunc("/", handler)
}

func handler(w http.ResponseWriter, r *http.Request) {
	//redirect_map := map[string]string {
	//	"libraries": "https://drone.io/dominic-mlab/m-lab.libraries?key=BV8KN727SQ1JMEK7DKIGSO97SLBDJL2O",
	//	"ns": "https://drone.io/dominic-mlab/m-lab.ns?key=S4MHVE51D5KN5SGK1IOV1TA0SGK21RBF",
	//}

	if r.Method == "POST" {
		c := appengine.NewContext(r)
		c.Debugf("Request: %#v", r)

		var b []byte;
		b, err := ioutil.ReadAll(r.Body)
		r.Body.Close()

		if err != nil {
			c.Errorf("Failed to read body: %v", err)
		} else {
			c.Debugf("Body: %s", string(b))
			//err := json.Unmarshal(b, &m)
		}
		// TODO: post to drone.io based on contents
		//http.Redirect(w, r, redirect_map["libraries"], http.StatusFound)
	}
}
