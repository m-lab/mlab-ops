#!/usr/local/bin/perl -w

use CGI qw/:standard/;

sub bysite {
    my $result;
    ($orga, $namea, $sitea, $macha) = reverse(split(/\./, $a));
    ($orgb, $nameb, $siteb, $machb) = reverse(split(/\./, $b));
    $result = $orga cmp $orgb;
    if (!$result) {
	$result = $namea cmp $nameb;
    }
    if (!$result) {
	$result = $sitea cmp $siteb;
    }
    if (!$result) {
	$result = $macha cmp $machb;
    }
    return $result;
}

my %name = ();
my %plugin_output = ();
my %current_state = ();
my %state_type = ();
my $DB = "/var/spool/nagios/status.dat";
my $state = 0;

CGI::ReadParse();

my @statlist = stat($DB);

if (!open(F, "< $DB")) {
    print "X-Open-Error: yes\n\n";
    exit;
}

my $curr_plugin_output = '';
my $curr_name = '';
my $curr_state = 0;
my $curr_state_type = 0;
my $curr_service_host = '';
my $curr_service_descr = '';

while (<F>) {
    
    # state 0 to state 1
    #
    if (($state == 0) && (/hoststatus {/)) {
	$curr_name = '';
	$curr_plugin_output = '';
	$curr_state = 0;
	$curr_state_type = 0;
	$state = 1;
	next;
    }

    # state 0 to state 2
    #
    if (($state == 0) && (/servicestatus {/)) {
	$curr_service_host = '';
	$curr_service_descr = '';
	$curr_name = '';
	$curr_plugin_output = '';
	$curr_state = 0;
	$curr_state_type = 0;
	$state = 2;
	next;
    }

    # state 1 to state 0
    #
    if (($state == 1) && (/}/)) {
	if ($curr_name ne '') {
	    $name{$curr_name} = 1;
	    $plugin_output{$curr_name} = $curr_plugin_output;
	    $current_state{$curr_name} = $curr_state;
	    $state_type{$curr_name} = $curr_state_type;
	}
	$state = 0;
    }

    # state 2 to state 0
    #
    if (($state == 2) && (/}/)) {
	if (($curr_service_host ne '') && ($curr_service_descr ne '')) {
	    $curr_name = $curr_service_host.'/'.$curr_service_descr;
	    $name{$curr_name} = 1;
	    $plugin_output{$curr_name} = $curr_plugin_output;
	    $current_state{$curr_name} = $curr_state;
	    $state_type{$curr_name} = $curr_state_type;
	}
	$state = 0;
    }

    # nothing to do while we're in state 0
    #
    next if $state == 0;

    # state 1, we're in a hoststatus
    #
    if ($state == 1) {
	if (/\shost_name=(.*)/) {
	    my $test_name = $1;
	    if (defined $in{slice_name} && $in{slice_name} eq 'ndt') {
		if ($test_name =~ /ndt\.iupui\.mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org$/) {
		    $curr_name = $test_name;
		}
	    } elsif (defined $in{slice_name} && $in{slice_name} eq 'neubot') {
		if ($test_name =~ /neubot\.mlab\.mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org$/) {
		    $curr_name = $test_name;
		}
	    } elsif (defined $in{slice_name} && $in{slice_name} eq 'mobiperf') {
		if ($test_name =~ /1\.michigan\.mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org$/) {
		    $curr_name = $test_name;
		}
	    } elsif (defined $in{slice_name} && $in{slice_name} eq 'npad') {
		if ($test_name =~ /npad\.iupui\.mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org$/) {
		    $curr_name = $test_name;
		}
	    } elsif (defined $in{slice_name} && $in{slice_name} eq 'glasnost') {
		if ($test_name =~ /broadband\.mpisws\.mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org$/) {
		    $curr_name = $test_name;
		}
	    } elsif (defined $in{slice_name} && $in{slice_name} eq 'all') {
		if ($test_name =~ /\.mlab\d\.[a-z]{3}\d\d.measurement-lab\.org$/) {
		    $curr_name = $test_name;
		}
	    } elsif (!defined($in{service_name}) && ($test_name =~ /^mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org$/)) {
		$curr_name = $test_name;
	    }
	    next;
	}
	if (/\splugin_output=(.*)/) {
	    $curr_plugin_output = $1;
	    next;
	}
	if (/\sstate_type=(\d)/) {
	    $curr_state_type = $1;
	    next;
	}
	if (/\scurrent_state=(\d)/) {
	    $curr_state = $1;
	    next;
	}
    }
    
    # state 2, we're in a servicestatus
    #
    if ($state == 2) {
	if (/\shost_name=(.*)/) {
	    $curr_service_host = $1;
	    next;
	}
	if (/\sservice_description=(.*)/) {
	    if (defined($in{service_name}) && $in{service_name} eq $1) {
		$curr_service_descr = $1;
	    }
	}
	if (/\splugin_output=(.*)/) {
	    $curr_plugin_output = $1;
	    next;
	}
	if (/\sstate_type=(\d)/) {
	    $curr_state_type = $1;
	    next;
	}
	if (/\scurrent_state=(\d)/) {
	    $curr_state = $1;
	    next;
	}
    }
}
close F;

print "Content-Type: text/plain\n";
print "X-Database-Mtime: ".$statlist[9]."\n";
print "\n";
foreach $n (sort bysite (keys %name)) {
    print $n;
    if (defined $in{show_state} && ($in{show_state} == 1)) {
	print ' '.$current_state{$n}.' '.$state_type{$n};
    }
    if (defined $in{plugin_output} && ($in{plugin_output} == 1)) {
	print ' '.$plugin_output{$n};
    }
    print "\n";
}
