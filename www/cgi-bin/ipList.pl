#!/usr/bin/env perl 

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
my %has_ipv6 = ();
my $DB = "/usr/local/www/data/mlab-host-ips.txt";
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

my %name_map = ( 'ndt' => 'ndt.iupui',
                 'neubot' => 'neubot.mlab',
                 'mobiperf' => '1.michigan',
                 'npad'   => 'npad.iupui',
                 'glasnost' => 'broadband.mpisws',
                 'all'      => '',
        );


while (<F>) {
  ($hostname, $ipv4, $ipv6) = split(/\,/, $_);
  if (defined $in{slice_name} && defined $name_map{$in{slice_name}} ) {
    $prefix=$name_map{$in{slice_name}};
    if ($hostname =~ /$prefix\.mlab\d\.[a-z]{3}\d\d\.measurement-lab\.org$/) {
      $name{$hostname} = 1;
      $has_ipv6{$hostname} = ($ipv6 == "" ? "0" : "1");
      $curr_name = $hostname;
    }
  }
}
close F;

print "Content-Type: text/plain\n";
print "X-Database-Mtime: ".$statlist[9]."\n";
print "\n";
foreach $n (sort bysite (keys %name)) {
    print $n;
    if (defined $in{show_state_ipv6} && ($in{show_state_ipv6} == 1)) {
        print ' '.$has_ipv6{$n};
    }
    print "\n";
}
